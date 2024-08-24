import streamlit as st
import openai
import requests
import json

# OpenAI APIキーの設定
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
else:
    st.error("OPENAI_API_KEYがsecretsに設定されていません。")

st.set_page_config(layout="wide")


# OpenAI APIキーの設定
openai.api_key = st.secrets["OPENAI_API_KEY"]
RAKUTEN_APP_ID = "1073975717553562237"

def get_wine_recommendations(product, occasion, recipient, budget):
    # ChatGPT 4を使用したワインのレコメンド
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",  # GPT-4モデルを指定
        messages=[
            {"role": "system", "content": "あなたはワインの専門家です。日本語で回答してください。"},
            {"role": "user", "content": f"Please recommend 5 wines for a {occasion} gift to a {recipient} with a budget of {budget}. "
                                        f"For each wine, provide the name followed by a colon, price, and a brief description (less than 300 characters) of its story or background."}
        ],
        max_tokens=700  # GPT-4では、出力の精度が高いので少し多めに
    )
    return response.choices[0].message.content

def format_recommendations(recommendations):
    # 商品名の後にコロンを付与する処理
    formatted_recommendations = []
    
    for line in recommendations.split("\n"):
        line = line.strip()
        if line:
            # 最初の単語を商品名として扱い、それ以降を説明とする
            parts = line.split(" ", 1)
            if len(parts) == 2:
                product_name = parts[0] + ":"  # 商品名にコロンを付ける
                description = parts[1]
                formatted_recommendations.append(f"{product_name} {description}")
            else:
                # 行が空の場合や、正しい形式でない場合
                formatted_recommendations.append(line)
    
    return "\n".join(formatted_recommendations)

def search_rakuten(product_name):
    # キーワードの長さを128文字に制限
    if len(product_name) > 128:
        product_name = product_name[:128]
    
    url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"
    
    params = {
        "format": "json",
        "keyword": product_name,  # selected_wineの商品名をここで使用
        "applicationId": RAKUTEN_APP_ID,
        "hits": 3
    }
    
    try:
        response = requests.get(url, params=params)
        
        # ステータスコードを確認
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"楽天APIリクエスト失敗: ステータスコード {response.status_code}")
            st.write(response.text)  # エラーメッセージを表示してデバッグ
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"楽天APIリクエスト中にエラーが発生しました: {e}")
        return None

# Streamlitのデザイン設計
st.title('🍷 ワインギフトレコメンドアプリ 🍷')

# 3列レイアウト作成
col1, col2, col3 = st.columns([1, 2, 3])

# 初期化: レコメンド結果を保持するための session_state を使用
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = None

# 左側にユーザー入力欄
with col1:
    st.header('🎁 ユーザー入力')
    with st.form(key='user_input_form'):
        product = st.text_input('商品', 'ワイン')
        occasion = st.text_input('目的', '昇進祝のプレゼント')
        recipient = st.text_input('プレゼント相手', '女性の上司')
        budget = st.text_input('金額', '50-100USD')
        
        submit_button = st.form_submit_button(label='レコメンドを表示')

# レコメンド結果を表示および保存
if submit_button:
    recommendations = get_wine_recommendations(product, occasion, recipient, budget)
    st.session_state.recommendations = recommendations

 # 中央にレコメンド結果
with col2:
    
    st.header('🍾 レコメンド結果')
    # レコメンド結果を取得
    if st.session_state.recommendations:
        recommendations = st.session_state.recommendations
        formatted_recommendations = format_recommendations(recommendations)

    # レコメンド結果が存在し、非空であるか確認してから表示
    if formatted_recommendations and len(formatted_recommendations) > 0:
        st.markdown(
            f"""
            <div style='background-color: black; color: white; padding: 10px; border-radius: 10px;'>
                {formatted_recommendations.replace('\n', '<br>')}
            </div>
            """, 
            unsafe_allow_html=True
        )
    else:
        st.write("レコメンド結果が見つかりませんでした。")

# 右側に商品選択と検索を表示
with col3:
    # 商品選択ボタン
    st.header("🛒 購入したいワインを選択してください")

    if st.session_state.recommendations:
        # 商品名を抽出して選択肢にする
        wine_options = []
        for line in st.session_state.recommendations.split("\n"):
            line = line.strip()
            if ":" in line:
                wine_name = line.split(":")[0].strip()  # コロンの前を商品名として抽出
                wine_options.append(wine_name)

        selected_wine = st.selectbox("ワインを選んでください", wine_options)

    # 楽天市場で商品を検索
    if st.button('楽天市場で検索'):
        st.header(f"'{selected_wine}' の検索結果")

        results = search_rakuten(selected_wine)
        if 'Items' in results:
            for item in results['Items'][:3]:
                item_info = item['Item']
                st.image(item_info['mediumImageUrls'][0]['imageUrl'], width=100)
                st.write(f"商品名: {item_info['itemName']}")
                st.write(f"価格: {item_info['itemPrice']} 円")
                st.write(f"[楽天市場で見る]({item_info['itemUrl']})")
        else:
            st.write("検索結果が見つかりませんでした。")
    else:
            st.write("表示できるワインの選択肢がありません。")
