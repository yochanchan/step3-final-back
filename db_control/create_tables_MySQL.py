import os
from pathlib import Path
from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker
from db_control.mymodels_MySQL import Base, Customers
from db_control.connect_MySQL import engine


def init_db():
    # インスペクターを作成
    inspector = inspect(engine)

    # 既存のテーブルを取得
    existing_tables = inspector.get_table_names()

    print("Checking tables...")

    # customersテーブルが存在しない場合は作成
    if 'customers' not in existing_tables:
        print("Creating tables >>> ")
        try:
            Base.metadata.create_all(bind=engine)
            print("Tables created successfully!")
        except Exception as e:
            print(f"Error creating tables: {e}")
            raise
    else:
        print("Tables already exist.")

# ここにインサート処理を追加！
def insert_sample_data():
    Session = sessionmaker(bind=engine)
    session = Session()

    customers = [
        Customers(customer_id="C1111", customer_name="ああさん", age=6, gender="男"),
        Customers(customer_id="C110", customer_name="桃太郎さん", age=30, gender="女"),
    ]

    try:
        session.add_all(customers)
        session.commit()
        print("Sample data inserted!")
    except Exception as e:
        print(f"Error inserting data: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    init_db()
    insert_sample_data()  # ← ここで呼び出す！
