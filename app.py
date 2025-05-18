# app.py
import streamlit as st
from openai import OpenAI
import yfinance as yf
from duckduckgo_search import DDGS

# Initialize OpenAI client with Streamlit secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def get_stock_info(symbol):
    """Fetch stock information using Yahoo Finance"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        return {
            'currentPrice': info.get('currentPrice', 'N/A'),
            'peRatio': info.get('trailingPE', 'N/A'),
            'marketCap': info.get('marketCap', 'N/A'),
            'analystRating': info.get('recommendationMean', 'N/A'),
            'dividendYield': info.get('dividendYield', 'N/A'),
            '52WeekHigh': info.get('fiftyTwoWeekHigh', 'N/A'),
            '52WeekLow': info.get('fiftyTwoWeekLow', 'N/A')
        }
    except Exception as e:
        return None

def get_news_articles(company_name):
    """Fetch recent news using DuckDuckGo"""
    with DDGS() as ddgs:
        return [result for result in ddgs.text(f"{company_name} stock news", max_results=5)]

def generate_response(query, stock_info, news_articles):
    """Generate AI response using OpenAI"""
    system_prompt = """You are an expert Indian financial analyst. Analyze the given stock information and news articles to answer the query.
    
    Stock Information:
    {stock_info}
    
    Recent News:
    {news_articles}
    
    Follow these guidelines:
    1. Present key metrics clearly
    2. Highlight relevant news impacts
    3. Mention market trends if applicable
    4. Maintain professional tone
    5. Never provide direct investment advice unless explicitly asked
    """
    
    user_prompt = f"Query: {query}\n\nProvide detailed analysis:"
    
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": system_prompt.format(
                stock_info=str(stock_info),
                news_articles="\n".join([f"- {article['title']}: {article['body']}" for article in news_articles])
            )},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content

# Streamlit UI
st.title("🇮🇳 AI Indian Financial Analyst")
st.write("Analyzing NSE/BSE stocks with real-time data and news")

col1, col2 = st.columns([1, 3])
with col1:
    symbol = st.text_input("Enter NSE/BSE Symbol (e.g., RELIANCE.NS, TCS.NS):").upper()
with col2:
    query = st.text_input("Your Query (e.g., 'Analysis of current valuation'):")

if st.button("Analyze"):
    if symbol and query:
        with st.spinner("Analyzing stock and market trends..."):
            # Get stock data
            stock_info = get_stock_info(symbol)
            if not stock_info:
                st.error("Invalid stock symbol or data unavailable")
                st.stop()
            
            # Get company news
            company_name = symbol.split('.')[0]
            news_articles = get_news_articles(company_name)
            
            # Generate AI response
            analysis = generate_response(query, stock_info, news_articles)
            
            # Display results
            st.subheader(f"Analysis for {symbol}")
            st.write(analysis)
            
            st.subheader("Key Metrics")
            col1, col2, col3 = st.columns(3)
            col1.metric("P/E Ratio", stock_info['peRatio'])
            col2.metric("Market Cap", f"₹{stock_info['marketCap']/1e7:.2f} Cr" if stock_info['marketCap'] != 'N/A' else 'N/A')
            col3.metric("Current Price", f"₹{stock_info['currentPrice']}")
            
            st.subheader("Recent News Highlights")
            for article in news_articles[:3]:
                st.write(f"📰 **{article['title']}**")
                st.caption(article['body'])
    else:
        st.warning("Please enter both stock symbol and query")

st.markdown("---")
st.caption("Note: This is an analytical tool and should not be considered as financial advice. Always do your own research.")
