import datetime, json, urllib.request, time, random

BOT_TOKEN = ""
HEADERS = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

KEYWORD_MAP = [
    {"kw":["苹果","apple","AAPL"],"code":"AAPL","type":"stock","name":"苹果","base":220.0},
    {"kw":["特斯拉","tesla","TSLA"],"code":"TSLA","type":"stock","name":"特斯拉","base":420.0},
    {"kw":["微软","msft","MSFT"],"code":"MSFT","type":"stock","name":"微软","base":450.0},
    {"kw":["谷歌","goog","GOOGL"],"code":"GOOGL","type":"stock","name":"谷歌","base":190.0},
    {"kw":["亚马逊","amzn","AMZN"],"code":"AMZN","type":"stock","name":"亚马逊","base":190.0},
    {"kw":["英伟达","nvda","NVDA"],"code":"NVDA","type":"stock","name":"英伟达","base":110.0},
    {"kw":["阿里巴巴","baba","BABA"],"code":"BABA","type":"stock","name":"阿里巴巴","base":75.0},
    {"kw":["拼多多","pdd","PDD"],"code":"PDD","type":"stock","name":"拼多多","base":140.0},
    {"kw":["蔚来","nio","NIO"],"code":"NIO","type":"stock","name":"蔚来","base":6.2},
    {"kw":["标普500ETF","标普500","SPY"],"code":"SPY","type":"fund","name":"标普500ETF","base":580.0},
    {"kw":["纳指100ETF","纳指100","QQQ"],"code":"QQQ","type":"fund","name":"纳指100ETF","base":480.0},
    {"kw":["罗素2000ETF","IWM"],"code":"IWM","type":"fund","name":"罗素2000ETF","base":210.0},
    {"kw":["黄金ETF","GLD"],"code":"GLD","type":"fund","name":"黄金ETF","base":230.0},
    {"kw":["投资级公司债","LQD"],"code":"LQD","type":"fund","name":"投资级公司债","base":110.0},
    {"kw":["高收益债","HYG"],"code":"HYG","type":"fund","name":"高收益债","base":80.0},
    {"kw":["碳信用ETF","KRBN"],"code":"KRBN","type":"fund","name":"碳信用ETF","base":28.0},
    {"kw":["黄金","GC=F"],"code":"GC=F","type":"commodity","name":"黄金","base":2400.0,"cgid":"gold"},
    {"kw":["白银","SI=F"],"code":"SI=F","type":"commodity","name":"白银","base":30.0,"cgid":"silver"},
    {"kw":["原油","石油","CL=F"],"code":"CL=F","type":"commodity","name":"原油","base":78.0,"cgid":"crude-oil"},
    {"kw":["铜","HG=F"],"code":"HG=F","type":"commodity","name":"铜","base":4.5},
    {"kw":["玉米","ZC=F"],"code":"ZC=F","type":"commodity","name":"玉米","base":4.0},
    {"kw":["天然气","NG=F"],"code":"NG=F","type":"commodity","name":"天然气","base":2.3},
    {"kw":["比特币","btc","BTC-USD"],"code":"BTC-USD","type":"crypto","name":"比特币","base":68000.0,"cgid":"bitcoin"},
    {"kw":["以太坊","eth","ETH-USD"],"code":"ETH-USD","type":"crypto","name":"以太坊","base":3400.0,"cgid":"ethereum"},
    {"kw":["狗狗币","doge","DOGE-USD"],"code":"DOGE-USD","type":"crypto","name":"狗狗币","base":0.3,"cgid":"dogecoin"},
    {"kw":["比特币信托","GBTC"],"code":"GBTC","type":"crypto","name":"比特币信托","base":42.0},
    {"kw":["长期美债","TLT"],"code":"TLT","type":"bond","name":"长期美债","base":92.0},
    {"kw":["中期美债","IEF"],"code":"IEF","type":"bond","name":"中期美债","base":104.0},
    {"kw":["短期美债","SHY"],"code":"SHY","type":"bond","name":"短期美债","base":82.0},
    {"kw":["通胀保护债","TIP"],"code":"TIP","type":"bond","name":"通胀保护债","base":112.0},
    {"kw":["欧元兑美元","EURUSD=X"],"code":"EURUSD=X","type":"forex","name":"欧元兑美元","base":1.08},
    {"kw":["美元兑日元","USDJPY=X"],"code":"USDJPY=X","type":"forex","name":"美元兑日元","base":145.0},
    {"kw":["澳元兑美元","AUDUSD=X"],"code":"AUDUSD=X","type":"forex","name":"澳元兑美元","base":0.65}
]

ASSET_ANALYZE_RULE={
    "stock":{"name":"股票","core":"基本面、行业、趋势、成交量","risk":"中高风险","tip":"结合均线、RSI、量价综合判断"},
    "fund":{"name":"基金","core":"底层资产、资金流向、折溢价","risk":"随底层资产变化","tip":"ETF看走势与成交，公募看净值与回撤"},
    "commodity":{"name":"大宗商品","core":"供需、地缘、美元、天气","risk":"高风险高波动","tip":"黄金看利率/避险，原油看供需/地缘"},
    "crypto":{"name":"加密货币","core":"流动性、监管、利率、市场情绪","risk":"极高风险","tip":"投机属性强，紧盯宏观与政策"},
    "bond":{"name":"债券","core":"利率、通胀、信用评级","risk":"低~中风险","tip":"美债与利率走势负相关"},
    "forex":{"name":"外汇","core":"利差、经济数据、央行政策","risk":"中高风险","tip":"流动性强，跟随货币强弱变化"}
}

SCORE_LEVEL={
    (8,10):"强势多头｜趋势向上，动能充足",
    (6,7.9):"偏多｜震荡偏强，适合持有",
    (4,5.9):"中性｜横盘震荡，方向不明",
    (2,3.9):"偏空｜震荡偏弱，谨慎操作",
    (0,1.9):"强势空头｜趋势向下，规避为主"
}

def parse_natural_input(text):
    text_low=text.lower()
    for item in KEYWORD_MAP:
        for kw in item["kw"]:
            if kw.lower() in text_low:
                return item
    return None

def fetch_yahoo(symbol):
    try:
        url=f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1mo"
        req=urllib.request.Request(url,headers=HEADERS)
        with urllib.request.urlopen(req,timeout=20) as res:
            raw=json.loads(res.read().decode("utf-8"))
        chart=raw["chart"]["result"][0]
        meta=chart["meta"]
        close=[c for c in chart["indicators"]["quote"][0]["close"] if c is not None]
        if len(close)<5:return None
        price=meta["regularMarketPrice"]
        prev=meta["previousClose"]
        chg_pct=round((price-prev)/prev*100,2)
        return {"price":price,"chg_pct":chg_pct,"currency":meta.get("currency","USD"),
                "5d":close[-5],"10d":close[-10],"series":close,"src":"yahoo"}
    except:
        return None

def fetch_coingecko(cgid):
    if not cgid:return None
    try:
        url=f"https://api.coingecko.com/api/v3/coins/{cgid}/market_chart?vs_currency=usd&days=30"
        req=urllib.request.Request(url,headers=HEADERS)
        with urllib.request.urlopen(req,timeout=20) as res:
            raw=json.loads(res.read().decode("utf-8"))
        prices=[p[1] for p in raw["prices"]]
        if len(prices)<5:return None
        price=prices[-1]
        prev=prices[-2]
        chg_pct=round((price-prev)/prev*100,2)
        return {"price":price,"chg_pct":chg_pct,"currency":"USD",
                "5d":prices[-5],"10d":prices[-10],"series":prices,"src":"coingecko"}
    except:
        return None

def gen_simulated(item):
    base=item["base"]
    series=[]
    now_price=base*(1+random.uniform(-0.08,0.08))
    prev_price=base*(1+random.uniform(-0.06,0.06))
    for _ in range(30):
        step=random.uniform(-base*0.02,base*0.02)
        base+=step
        series.append(round(base,2))
    chg_pct=round((now_price-prev_price)/prev_price*100,2)
    return {"price":round(now_price,2),"chg_pct":chg_pct,"currency":"USD",
            "5d":series[-5],"10d":series[-10],"series":series,"src":"sim"}

def fetch_3source(item):
    data=fetch_yahoo(item["code"])
    if data:return data
    if "cgid" in item:
        data=fetch_coingecko(item["cgid"])
        if data:return data
    return gen_simulated(item)

def trend_score(p,p5,p10):
    if p>p5>p10:return 4,"上升趋势"
    elif p<p5<p10:return 0,"下降趋势"
    elif p>p10 and p<=p5:return 2.5,"震荡偏强"
    elif p<p10 and p>=p5:return 1.5,"震荡偏弱"
    return 2,"横盘震荡"

def momentum_score(c):
    if c>=3:return 3,"强势上涨，动能充足"
    elif 0<=c<3:return 2,"温和上涨"
    elif -3<c<0:return 1,"小幅回落"
    return 0,"弱势下跌，动能走弱"

def rsi_score(series):
    period=14
    if len(series)<period:return 50,2,"中性区"
    gains,losses=[],[]
    for i in range(1,period):
        diff=series[i]-series[i-1]
        gains.append(diff if diff>0 else 0)
        losses.append(-diff if diff<0 else 0)
    avg_gain=sum(gains)/period
    avg_loss=sum(losses)/period
    if avg_loss==0:rsi=100
    elif avg_gain==0:rsi=0
    else:
        rs=avg_gain/avg_loss
        rsi=round(100-100/(1+rs),2)
    if rsi>=70:return rsi,1,"超买区间"
    elif rsi<=30:return rsi,3,"超卖区间"
    return rsi,2,"中性区"

def total_analysis(data):
    t_sc,t_txt=trend_score(data["price"],data["5d"],data["10d"])
    m_sc,m_txt=momentum_score(data["chg_pct"])
    rsi_val,r_sc,rsi_txt=rsi_score(data["series"])
    return round(t_sc+m_sc+r_sc,1),t_txt,m_txt,rsi_val,rsi_txt

def ai_editor_view(total_score,name):
    pct=(total_score-5)*2
    pct=max(-10,min(10,pct))
    if pct>0:
        return f"📈 AI总编辑看法：{name}短期大概率上行，预计上涨 {pct:.1f}% 以内，逢低可轻仓关注。"
    elif pct<0:
        return f"📉 AI总编辑看法：{name}短期偏弱，预计下跌 {abs(pct):.1f}% 以内，建议观望或控制仓位。"
    else:
        return f"➡️ AI总编辑看法：{name}短期方向不明，震荡概率大，波动区间±5%，耐心等待突破。"

def build_report(name,data,asset_type,ask_pred=False):
    total_score,trend_txt,mom_txt,rsi_val,rsi_txt=total_analysis(data)
    rule=ASSET_ANALYZE_RULE.get(asset_type,{"name":"未知品类","core":"无","risk":"未知","tip":"无"})
    judge=""
    for (low,high),desc in SCORE_LEVEL.items():
        if low<=total_score<=high:
            judge=desc
            break
    now=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    chg=data["chg_pct"]
    chg_str=f"+{chg}%" if chg>0 else f"{chg}%"
    dir_txt="上涨📈" if chg>0 else "下跌📉"
    src_note=""
    if data["src"]=="sim":
        src_note="⚠️ 网络异常，本次为模拟数据，仅供参考"
    elif data["src"]=="coingecko":
        src_note="ℹ️ 数据来源：CoinGecko"
    elif data["src"]=="yahoo":
        src_note="ℹ️ 数据来源：Yahoo Finance"

    report=f"""📊 {name} 近期走势分析
更新时间：{now}
所属板块：{rule['name']}

💵 价格：{data['currency']} {data['price']}
日内：{chg_str} {dir_txt}

📉 趋势：{trend_txt}
⚡ 动能：{mom_txt}
📶 RSI：{rsi_val}（{rsi_txt}）

📊 综合评分：{total_score}/10
结论：{judge}

📌 核心：{rule['core']}
风险：{rule['risk']}
提示：{rule['tip']}
{src_note}"""
    if ask_pred:
        report+="\n\n"+ai_editor_view(total_score,name)
    report+="\n⚠️ 不构成投资建议"
    return report

def handle_message(update,context):
    text=update.message.text.strip()
    item=parse_natural_input(text)
    if not item:
        update.message.reply_text("❌ 未识别标的\n示例：以太坊近期走势、苹果股价、黄金会涨吗")
        return
    ask_pred=any(k in text for k in ["建议","会涨吗","走向","预测","看法","怎么看"])
    update.message.reply_text(f"⏳ 分析 {item['name']}...")
    data=fetch_3source(item)
    report=build_report(item["name"],data,item["type"],ask_pred)
    update.message.reply_text(report)

def start_cmd(update,context):
    welcome="""👋 三数据源行情机器人（AI预测版）
✅ 自然语言直接问
✅ 数据源：Yahoo→CoinGecko→本地模拟
✅ AI总编辑：±10%明确预测

示例：
以太坊近期走势
黄金会涨吗
特斯拉怎么看
比特币短期建议

覆盖：股票/ETF/商品/加密/债券/外汇"""
    update.message.reply_text(welcome)

def main():
    from telegram.ext import Updater,CommandHandler,MessageHandler,Filters
    import os
    global BOT_TOKEN
    BOT_TOKEN=os.getenv("BOT_TOKEN") or BOT_TOKEN
    updater=Updater(BOT_TOKEN)
    dp=updater.dispatcher
    dp.add_handler(CommandHandler("start",start_cmd))
    dp.add_handler(MessageHandler(Filters.text&~Filters.command,handle_message))
    updater.start_polling()
    print("✅ 三数据源+AI预测版已启动")
    updater.idle()

if __name__=="__main__":
    main()
