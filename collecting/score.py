from transformers import BertTokenizer, BertForSequenceClassification
from transformers import pipeline
import psycopg2

# DB 연결부
conn = psycopg2.connect(host="localhost", dbname="postgres",
                        user="postgres", password="220602", port=5432)
cur = conn.cursor()

cur.execute('select id, trnsltd from "AIS".news where trnsltd is not null and score is null')
proyet = cur.fetchall()
for p in proyet:
    id, trnsltd = p
    scorelist = []
    trlist = trnsltd.split('***')
    
    # 점수 매기기 https://huggingface.co/ahmedrachid/FinancialBERT-Sentiment-Analysis
    model = BertForSequenceClassification.from_pretrained(
        "ahmedrachid/FinancialBERT-Sentiment-Analysis", num_labels=3)
    tokenizer = BertTokenizer.from_pretrained(
        "ahmedrachid/FinancialBERT-Sentiment-Analysis")
    nlp = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
    print("계산중...")
    scorerslt = 0
    for t in trlist:
        anls = nlp(t)
        label, score = anls[0]['label'], anls[0]['score']
        if label == 'neutral':
            pass
        elif label == 'positive':
            scorerslt += score
        elif label == 'negative':
            scorerslt -= score
    scorerslt/=len(trlist)
    cur.execute('update "AIS".news set score = %s where id = %s', [
                scorerslt, id])
    conn.commit()