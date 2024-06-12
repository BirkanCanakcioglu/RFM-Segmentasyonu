#RFM ile Müşteri Segmentasyonu

#Aşamalar

# 1. İş Problemi (Business Problem)
###############################################################

# Bir e-ticaret şirketi müşterilerini segmentlere ayırıp bu segmentlere göre
# pazarlama stratejileri belirlemek istiyor.

# Veri Seti Hikayesi
# https://archive.ics.uci.edu/ml/datasets/Online+Retail+II

# Online Retail II isimli veri seti İngiltere merkezli online bir satış mağazasının
# 01/12/2009 - 09/12/2011 tarihleri arasındaki satışlarını içeriyor.

# Değişkenler
#
# InvoiceNo: Fatura numarası. Her işleme yani faturaya ait eşsiz numara. C ile başlıyorsa iptal edilen işlem.
# StockCode: Ürün kodu. Her bir ürün için eşsiz numara.
# Description: Ürün ismi
# Quantity: Ürün adedi. Faturalardaki ürünlerden kaçar tane satıldığını ifade etmektedir.
# InvoiceDate: Fatura tarihi ve zamanı.
# UnitPrice: Ürün fiyatı (Sterlin cinsinden)
# CustomerID: Eşsiz müşteri numarası
# Country: Ülke ismi. Müşterinin yaşadığı ülke.

#2. Veriyi Anlama(Data Understanding)

df.info()
import datetime as dt
import pandas as pd
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option("display.float_format", lambda x: "%.5f" % x)

df_ = pd.read_excel("/Users/arwen/Desktop/Miuul Mentor/Week 3/Kurs Materyalleri(CRM Analitiği)/datasets/online_retail_II.xlsx", sheet_name="Year 2009-2010")
df = df_.copy()

df.head()
df.shape
df.isnull().sum()   #eksik değer gözlemleyelim

#eşsiz ürün sayısı nedir?
df["Description"].nunique()
#df["StockCode"].nunique()

#her bir ürün faturalarda kaçar defa geçmiş?
df["Description"].value_counts().head(20)

#her bir ürün kaçar tane satılmış?
df.groupby("Description").agg({"Quantity" : "sum"}).head(20)
df.groupby("Description").agg({"Quantity" : "sum"}).sort_values("Quantity", ascending=False).head()

#kaçar tane eşsiz fatura kesilmiş?
df["Invoice"].nunique()

#Fatura başına toplam ne kadar para kazanılmıştır?
df["TotalPrice"] = df["Quantity"] * df["Price"]
df.head()
df.groupby("Invoice").agg({"TotalPrice" : "sum"}).head()

#3. Veriyi Hazırlama(Data Preparation)

df.shape
df.isnull().sum()  #verimizde eksik değerler var

#customer id'lerin eksik değerleri oldukça çok
#o yüzden onları veri setimizden çıkartalım
df.dropna(inplace=True) #eksik değerleri dropna ile çıkardık ve True ile kalıcı hale getirdik

df.describe().T
#iade edilen ürünlerin başında "C" ifadesi var ve bunlar veri setinde
#negatif değer olarak görülüp veri setini bozan değerler
#bunların dışındaki değerlere odaklanmalıyız!
df = df[~df["Invoice"].str.contains("C", na=False)]
df.describe().T

#4. RFM Metriklerinin Hesaplanması(Calculating RFM Metrics)

#Recency, Frequency, Monetary(Her bir müşteri özelinde)

df.head()

#analizi yaptığımız günü belirleyelim
df["InvoiceDate"].max()
today_date = dt.datetime(2010, 12, 11)

rfm = df.groupby("Customer ID").agg({"InvoiceDate": lambda InvoiceDate: (today_date - InvoiceDate.max()).days,
                                    "Invoice":     lambda Invoice: Invoice.nunique(),
                                    "TotalPrice":  lambda TotalPrice: TotalPrice.sum()})


rfm.head()
rfm.columns= ["Recency", "Frequency", "Monetary"]
rfm.describe().T

#monetary değeri sıfır olan değerler var onları istemiyoruz
rfm = rfm[rfm["Monetary"] > 0]
rfm.shape

#5. RFM Skorlarının Hesaplanması(Calculating RFM Scores)

#Recency Skorunu hesaplayalım
rfm["recency_score"] = pd.qcut(rfm["Recency"], 5, labels=[5, 4, 3, 2, 1])
#qcut elimizdeki değişkeni çeyrek değerlerine göre böler!(küçükten büyüğe göre sıralar öncelikle)
rfm.head(20)

#Monetary Skorunu hesaplayalım
rfm["monetary_score"] = pd.qcut(rfm["Monetary"], 5, labels=[1, 2, 3, 4, 5])

#Frequency Skorunu hesaplayalım
rfm["frequency_score"] = pd.qcut(rfm["Frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])

#R-F değerlerini bir araya getirmemiz gerekiyor
rfm["RFM_SCORE"] = (rfm["recency_score"].astype(str) + 
                    rfm["frequency_score"].astype(str))

rfm.describe().T
#Şampiyon müşterilerimizi görüntüleyelim
rfm[rfm["RFM_SCORE"] == "55"]

#6. RFM Segmentlerinin Oluşturulması(Creating & Analysing RFM Segments)

#regex işlemlerini kullanacağız(regular expression)

#RFM İsimlendirmesi
seg_map = {
    r'[1-2][1-2]': 'hibernating',
    r'[1-2][3-4]': 'at_Risk',
    r'[1-2]5': 'cant_loose',
    r'3[1-2]': 'about_to_sleep',
    r'33': 'need_attention',
    r'[3-4][4-5]': 'loyal_customers',
    r'41': 'promising',
    r'51': 'new_customers',
    r'[4-5][2-3]': 'potential_loyalists',
    r'5[4-5]': 'champions'
}

#replace metodu; belirtilen sütundaki değerleri değiştirmek için kullanılır
#regex=True parametresi, haritalama işlemlerinde düzenli ifadelerin
#kullanılabileceğini belirtir.
rfm["segment"] = rfm["RFM_SCORE"].replace(seg_map, regex=True)

#segmentler arasında karşılaştırma yapalım
rfm[["segment", "Recency", "Frequency", "Monetary"]].groupby("segment").agg(["mean", "count"])

#need_attention durumunda olan kişilere odaklanalım
rfm[rfm["segment"] == "need_attention"].head(10)
rfm[rfm["segment"] == "need_attention"].index

#bu işlemi dışarı çıkartalım
new_df = pd.DataFrame()
new_df["new_customer_id"] = rfm[rfm["segment"] == "new_customers"].index
new_df["new_customer_id"] = new_df["new_customer_id"].astype(int)

new_df.to_csv("new_customers.csv")

rfm.to_csv("rfm.csv")

#7. Tüm İşlemleri Fonksiyonlaştıralım(Script)

def create_rfm(dataframe, csv=False):

    # VERIYI HAZIRLAMA
    dataframe["TotalPrice"] = dataframe["Quantity"] * dataframe["Price"]
    dataframe.dropna(inplace=True)
    dataframe = dataframe[~dataframe["Invoice"].str.contains("C", na=False)]

    # RFM METRIKLERININ HESAPLANMASI
    today_date = dt.datetime(2011, 12, 11)
    rfm = dataframe.groupby('Customer ID').agg({'InvoiceDate': lambda date: (today_date - date.max()).days,
                                                'Invoice': lambda num: num.nunique(),
                                                "TotalPrice": lambda price: price.sum()})
    rfm.columns = ['recency', 'frequency', "monetary"]
    rfm = rfm[(rfm['monetary'] > 0)]

    # RFM SKORLARININ HESAPLANMASI
    rfm["recency_score"] = pd.qcut(rfm['recency'], 5, labels=[5, 4, 3, 2, 1])
    rfm["frequency_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
    rfm["monetary_score"] = pd.qcut(rfm['monetary'], 5, labels=[1, 2, 3, 4, 5])

    # cltv_df skorları kategorik değere dönüştürülüp df'e eklendi
    rfm["RFM_SCORE"] = (rfm['recency_score'].astype(str) +
                        rfm['frequency_score'].astype(str))


    # SEGMENTLERIN ISIMLENDIRILMESI
    seg_map = {
        r'[1-2][1-2]': 'hibernating',
        r'[1-2][3-4]': 'at_risk',
        r'[1-2]5': 'cant_loose',
        r'3[1-2]': 'about_to_sleep',
        r'33': 'need_attention',
        r'[3-4][4-5]': 'loyal_customers',
        r'41': 'promising',
        r'51': 'new_customers',
        r'[4-5][2-3]': 'potential_loyalists',
        r'5[4-5]': 'champions'
    }

    rfm['segment'] = rfm['RFM_SCORE'].replace(seg_map, regex=True)
    rfm = rfm[["recency", "frequency", "monetary", "segment"]]
    rfm.index = rfm.index.astype(int)

    if csv:
        rfm.to_csv("rfm.csv")

    return rfm

df = df_.copy()

rfm_new = create_rfm(df, csv=True)
