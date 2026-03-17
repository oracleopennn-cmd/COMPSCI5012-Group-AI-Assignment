import os
import sys
import sqlite3
import re

# ================= 配置区域 =================
_script_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_script_dir, 'db.sqlite3')
TABLE_NAME = 'web_learningpathitem'
BAD_REF_TABLE = 'web_resource__old'
# 需要修复 web_group__old 引用的表（外键指向不存在的表会导致 no such table）
GROUP_TABLES = ('web_groupmember', 'web_groupmessage', 'web_groupjoinrequest', 'web_groupinvite')
BAD_REF_GROUP = 'web_group__old'
GOOD_REF_GROUP = 'web_group'
FK_COLUMN = 'resource_id'  # 根据报错推断出的外键列名


# ===========================================

def fix_table():
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件未找到: {DB_PATH}")
        return

    print(f"🔗 正在连接数据库: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. 获取原始建表语句
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{TABLE_NAME}';")
        result = cursor.fetchone()
        if not result:
            print(f"❌ 表 '{TABLE_NAME}' 不存在。")
            return

        original_sql = result[0]
        print(f"\n📜 表 '{TABLE_NAME}' 的原始建表语句:")
        print(original_sql)

        if BAD_REF_TABLE not in original_sql:
            print(f"\n✅ 未发现对 '{BAD_REF_TABLE}' 的引用。可能已修复或表名有误。")
            # 即使没发现引用，也可能是因为数据本身脏但约束没写死？
            # 但报错明确说是 IntegrityError，通常意味着有约束。
            # 如果这里没发现，我们尝试直接删除脏数据行作为备选方案。
            check_and_delete_orphans(cursor, conn)
            return

        # 2. 构建清理逻辑 (移除 REFERENCES 部分)
        # 匹配模式：REFERENCES "web_resource__old" ("id") 及其前面的空格
        pattern = r'\s+REFERENCES\s+"?' + re.escape(BAD_REF_TABLE) + r'"?\s*\([^)]+\)'

        cleaned_sql = re.sub(pattern, '', original_sql, flags=re.IGNORECASE)

        if cleaned_sql == original_sql:
            print("\n❌ 正则替换未生效。尝试直接删除脏数据行...")
            check_and_delete_orphans(cursor, conn)
            return

        print("\n📝 清理后的建表语句 (移除了损坏的外键约束):")
        print(cleaned_sql)

        # 3. 用户确认
        confirm = input(f"\n❓ 是否执行修复？这将移除指向 '{BAD_REF_TABLE}' 的外键约束并重建表。输入 yes 确认: ")
        if confirm.lower() != 'yes':
            print("操作已取消。")
            return

        print("🔄 开始重建表...")

        # 4. 执行重建流程
        cursor.execute("PRAGMA foreign_keys=OFF;")
        cursor.execute("BEGIN TRANSACTION;")

        # 4.1 备份索引
        cursor.execute(
            f"SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='{TABLE_NAME}' AND sql IS NOT NULL;")
        index_defs = [row[0] for row in cursor.fetchall()]

        # 4.2 创建新表
        new_table_name = f"{TABLE_NAME}_new"
        create_new_sql = cleaned_sql.replace(TABLE_NAME, new_table_name, 1)
        cursor.execute(create_new_sql)
        print(f"   ✅ 新表 '{new_table_name}' 创建成功。")

        # 4.3 复制数据
        cursor.execute(f"PRAGMA table_info({TABLE_NAME});")
        cols_info = cursor.fetchall()
        col_names = [info[1] for info in cols_info]
        quoted_cols = ', '.join([f'"{c}"' for c in col_names])

        cursor.execute(f"INSERT INTO {new_table_name} ({quoted_cols}) SELECT {quoted_cols} FROM {TABLE_NAME};")
        count = cursor.rowcount
        print(f"   📥 已复制 {count} 行数据。")

        # 4.4 删除旧表
        cursor.execute(f"DROP TABLE {TABLE_NAME};")

        # 4.5 重命名
        cursor.execute(f"ALTER TABLE {new_table_name} RENAME TO {TABLE_NAME};")

        # 4.6 恢复索引
        for idx_sql in index_defs:
            try:
                cursor.execute(idx_sql)
            except Exception as e:
                pass  # 忽略索引恢复错误

        cursor.execute("COMMIT;")
        cursor.execute("PRAGMA foreign_keys=ON;")

        print("\n✅ 表结构修复完成！")

    except Exception as e:
        conn.rollback()
        print(f"\n💥 发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


def check_and_delete_orphans(cursor, conn):
    """备选方案：如果无法重建表，尝试直接删除导致报错的脏数据行"""
    print(f"\n⚠️  尝试直接删除导致冲突的脏数据行...")
    print(f"   报错提到：主键 19 的行，resource_id = 51 无效。")

    # 验证一下
    cursor.execute(f"SELECT id, resource_id FROM {TABLE_NAME} WHERE id = 19;")
    row = cursor.fetchone()
    if row:
        print(f"   找到问题行: ID={row[0]}, resource_id={row[1]}")
        confirm = input(f"   是否删除这一行 (ID=19) 以绕过错误？(yes/no): ")
        if confirm.lower() == 'yes':
            cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE id = 19;")
            conn.commit()
            print("   ✅ 已删除问题行。请重新运行 migrate。")
        else:
            print("   操作取消。")
    else:
        print("   未找到 ID=19 的行，可能数据已变化。")


def fix_group_tables():
    """Fix SQLite tables that reference web_group__old (replace with web_group)."""
    if not os.path.exists(DB_PATH):
        print("Database not found: {}".format(DB_PATH))
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        for table_name in GROUP_TABLES:
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
            row = cursor.fetchone()
            if not row or not row[0]:
                continue
            original_sql = row[0]
            if BAD_REF_GROUP not in original_sql:
                continue
            cleaned_sql = original_sql.replace(BAD_REF_GROUP, GOOD_REF_GROUP)
            if cleaned_sql == original_sql:
                continue
            print("Fixing table: {} (replace {} with {})".format(table_name, BAD_REF_GROUP, GOOD_REF_GROUP))
            cursor.execute("PRAGMA foreign_keys=OFF;")
            cursor.execute("BEGIN TRANSACTION;")
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name=? AND sql IS NOT NULL;", (table_name,))
            index_defs = [r[0] for r in cursor.fetchall()]
            new_name = table_name + "_new"
            create_sql = cleaned_sql.replace(table_name, new_name, 1)
            cursor.execute(create_sql)
            cursor.execute("PRAGMA table_info({});".format(table_name))
            cols = [c[1] for c in cursor.fetchall()]
            quoted = ", ".join('"{}"'.format(c) for c in cols)
            cursor.execute("INSERT INTO {} ({}) SELECT {} FROM {};".format(new_name, quoted, quoted, table_name))
            cursor.execute("DROP TABLE {};".format(table_name))
            cursor.execute("ALTER TABLE {} RENAME TO {};".format(new_name, table_name))
            for idx_sql in index_defs:
                try:
                    cursor.execute(idx_sql)
                except Exception:
                    pass
            cursor.execute("COMMIT;")
            cursor.execute("PRAGMA foreign_keys=ON;")
            print("  OK: {} fixed.".format(table_name))
    except Exception as e:
        conn.rollback()
        print("Error: {}".format(e))
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "group":
        fix_group_tables()
    else:
        fix_table()
        print("\nTo fix 'no such table: web_group__old' run: python fix_constraint.py group")