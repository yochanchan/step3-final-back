from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import requests
import json
from db_control import crud, mymodels_MySQL
from openai import OpenAI
from textwrap import dedent

##### Customerの型定義
class Customer(BaseModel):
    customer_id: str = Field(..., min_length=1, description="必須")
    customer_name: str
    age: int
    gender: str

app = FastAPI()

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def index():
    return {"message": "FastAPI top page!"}


##### insert　this.Customerをinsertする。Customerが型ヒントですよ。
@app.post("/customers")
def create_customer(customer: Customer):
    values = customer.dict()
    tmp = crud.myinsert(mymodels_MySQL.Customers, values)
    result = crud.myselect(mymodels_MySQL.Customers, values.get("customer_id"))

    if result:
        result_obj = json.loads(result)
        return result_obj if result_obj else None
    return HTTPException(status_code=402, detail="Something wrong")



@app.get("/customers")
def read_one_customer(customer_id: str = Query(...)):
    result = crud.myselect(mymodels_MySQL.Customers, customer_id)
    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")
    result_obj = json.loads(result)
    return result_obj[0] if result_obj else None


@app.get("/allcustomers")
def read_all_customer():
    result = crud.myselectAll(mymodels_MySQL.Customers)
    # 結果がNoneの場合は空配列を返す
    if not result:
        return []
    # JSON文字列をPythonオブジェクトに変換
    return json.loads(result)


@app.put("/customers")
def update_customer(customer: Customer):
    values = customer.dict()
    values_original = values.copy()
    tmp = crud.myupdate(mymodels_MySQL.Customers, values)
    result = crud.myselect(mymodels_MySQL.Customers, values_original.get("customer_id"))
    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")
    result_obj = json.loads(result)
    return result_obj[0] if result_obj else None


@app.delete("/customers")
def delete_customer(customer_id: str = Query(...)):
    result = crud.mydelete(mymodels_MySQL.Customers, customer_id)
    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"customer_id": customer_id, "status": "deleted"}


@app.get("/fetchtest")
def fetchtest():
    response = requests.get('https://jsonplaceholder.typicode.com/users')
    return response.json()

@app.get("/search")
def search(
    company_name: str | None = None,
    address: str | None = None,
    industry: str | None = None,
    rep_name: str | None = None,
    ):

    about = {
        "company_name": company_name,
        "address": address,
        "industry": industry,
        "rep_name": rep_name,
    }

    client = OpenAI()

###6社の制限は、10社とかにした方がいいかも
    prompt = dedent(f"""
        あなたは、企業調査のプロフェッショナルです。日本中の企業概要を調べることが得意であり、インターネットから最新かつ正確な情報を取得することができます。
        以下の【input情報】をもとに、条件にマッチする企業を探してください。なお、【input情報】には曖昧な部分や省略形が含まれている可能性があります。例えば、『株式会社日立製作所』について『company_name: 日立』と input されていたり、『industry: 家電メーカーと思われる』と入力されているようなケースがあります。
        検索企業数は 6 社で打ち切り、7 社以上については調べる必要はありません。
        検索結果の企業概要を【output情報】のとおりに出力してください。なお、不明な点があるときは、創作せず、必ず「情報なし」と記載するようにしてください。
        
        【出力要求（遵守事項）】
        ・あなたの回答は必ず有効な JSON（UTF-8, ダブルクォート, 末尾カンマ禁止）で、かつ、配列として出力してください。
        ・配列として出力するため、必ず [ で始まり、 ] で終わるよう出力してください。
        ・『以下の企業が条件に一致しました。』といった、説明やコメントは絶対につけてはいけません。

        【input情報】
        {about}

        【output情報】（2社以上がマッチしたときのサンプル）
        [
            {{
                "company_name": "株式会社サンプル",
                "industry": "情報通信業",
                "address": "東京都千代田区丸の内1-1-1",
                "est_date": "2010-04-01",
                "rep_name": "山田 太郎",
                "rep_birthday": "1975-06-15"
            }},
            {{
                "company_name": "例示製造株式会社",
                "industry": "製造業",
                "address": "大阪府大阪市西区2-3-4",
                "est_date": "2005-09-20",
                "rep_name": "鈴木 花子",
                "rep_birthday": "1980-11-30"
            }}
        ]

        【output情報】（1社のみがマッチしたときのサンプル）
        [
            {{
                "company_name": "株式会社サンプル",
                "industry": "情報通信業",
                "address": "東京都千代田区丸の内1-1-1",
                "est_date": "2010-04-01",
                "rep_name": "山田 太郎",
                "rep_birthday": "1975-06-15"
            }}
        ]

        【output情報】（1社もマッチしなかったときのサンプル）
        [
            {{
                "company_name": "見つかりませんでした",
                "industry": "情報なし",
                "address": "情報なし",
                "est_date": "情報なし",
                "rep_name": "情報なし",
                "rep_birthday": "情報なし"
            }}
        ]
    """).strip()
    
    response = client.responses.create(
        model="gpt-4.1",
        tools=[{ "type": "web_search_preview" }],
        input= prompt,
    )
    raw_json = response.output_text
    print(raw_json)

    # 空の結果
    if not raw_json:
        raise HTTPException(
            status_code=404,
            detail="検索結果を取得できませんでした。"
        )
    
    # ③ JSON 文字列をパースして **リスト** に変換
    try:
        answer = json.loads(raw_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="JSON パースに失敗しました")

    # 6 社以上ヒットした場合
    if len(answer) > 5:
        raise HTTPException(
            status_code=422,
            detail="検索結果が 6 社以上あります。最大 5 社までにしてください。"
        )

    return answer
