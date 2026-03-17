import os
import sys
import django

# ================= 配置区域 =================
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
# 将 django_python 加入路径，确保能导入 backend 模块
_script_dir = os.path.dirname(os.path.abspath(__file__))
_django_dir = os.path.join(_script_dir, 'django_python')
sys.path.insert(0, _django_dir)

try:
    django.setup()
except Exception as e:
    print(f"❌ Django 初始化失败: {e}")
    print(
        "提示：请检查上面的 DJANGO_SETTINGS_MODULE 是否设置正确（例如可能是 'django_python.settings' 或 'config.settings'）")
    sys.exit(1)

from django.db import connection


def fix_database():
    print("🔍 正在连接数据库...")
    with connection.cursor() as cursor:
        try:
            # 1. 获取有效的组 ID（优先使用 web_group，迁移时可能为 web_group__old）
            source_table = 'web_groupmember'
            target_table = 'web_group'

            # 检查 web_group 是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('web_group', 'web_group__old');")
            tables = [row[0] for row in cursor.fetchall()]
            if 'web_group' in tables:
                target_table = 'web_group'
            elif 'web_group__old' in tables:
                target_table = 'web_group__old'
            else:
                print("❌ 未找到 web_group 或 web_group__old 表。")
                return

            print(f"📋 从表 '{target_table}' 获取有效组 ID...")
            cursor.execute("SELECT id FROM {}".format(target_table))
            valid_ids = set(row[0] for row in cursor.fetchall())
            print(f"   找到 {len(valid_ids)} 个有效的组 ID")

            # 2. 查找 source_table 中所有指向无效 ID 的记录
            print(f"🔎 扫描表 '{source_table}' 寻找外键断裂的数据...")
            cursor.execute(f"SELECT id, group_id FROM {source_table}")
            all_members = cursor.fetchall()

            orphan_records = []
            for member_id, group_id in all_members:
                if group_id not in valid_ids:
                    orphan_records.append((member_id, group_id))

            if not orphan_records:
                print("✅ 太好了！未发现外键断裂的数据。数据库一致性检查通过。")
                print("   你可以直接运行 'python manage.py migrate' 了。")
                return

            print(f"\n⚠️  发现 {len(orphan_records)} 条‘孤儿’数据（指向不存在的组）：")
            for mid, gid in orphan_records:
                print(f"   - 成员记录 ID: {mid} -> 引用的组 ID: {gid} (不存在)")

            # 3. 执行删除操作（支持 --yes 参数非交互执行）
            if '--yes' in sys.argv:
                confirm = 'yes'
            else:
                confirm = input("\n❓ 是否删除这些无效数据以修复数据库？(输入 yes 确认): ").strip().lower()
            if confirm.lower() == 'yes':
                print("🗑️  正在删除无效数据...")
                for mid, _ in orphan_records:
                    cursor.execute(f"DELETE FROM {source_table} WHERE id = ?", [mid])

                connection.commit()  # 提交事务
                print("✅ 修复成功！无效数据已清除。")
                print("\n🚀 现在请重新运行迁移命令:")
                print("   python manage.py migrate")
            else:
                print("❌ 操作已取消。数据库未修改。")

        except Exception as e:
            print(f"\n💥 执行过程中发生错误: {e}")
            print("可能原因：")
            print("1. 表名 'web_group__old' 或 'web_groupmember' 不正确。")
            print("2. 数据库文件损坏。")
            print("请检查报错详情或确认模型定义。")


if __name__ == "__main__":
    fix_database()