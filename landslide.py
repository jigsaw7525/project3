from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import  time
from glob import glob
import os
import sqlite3
import matplotlib.pyplot as plt
#中文基本設定 (！影響全部程式！)
plt.rcParams["font.family"]="Microsoft YaHei"
plt.rcParams["font.size"]= 14

# ===================== 爬資料 =====================
url = "https://246.swcb.gov.tw/Info/Potential"
driver = webdriver.Chrome()
driver.get(url)
time.sleep(2)

pages_remaining = True
page_num = 1

csv_dir = "csv" #資料夾名稱
if not os.path.exists(csv_dir):
    os.mkdir(csv_dir)
    
pic_dir = "pic" #資料夾名稱
if not os.path.exists(pic_dir):
    os.mkdir(pic_dir)
    
while pages_remaining :
    #使用Beautiful Soup剖析HTML網頁
    soup = BeautifulSoup(driver.page_source,"lxml")
    table = soup.select_one("#IndexPartialSection > table")
    
    df = pd.read_html(str(table))
    print(df[0])
    
    df[0].to_csv((r"D:\lcc\xz_python2\專題\csv\data") + str(page_num) + ".csv")    
    print("儲存頁面",page_num)
    try :
        #自動下一頁
        next_link = driver.find_element_by_partial_link_text("»")
        next_link.click()
        time.sleep(2)
        if page_num < 173:
            page_num += 1
        else :
            pages_remaining = False
    except Exception :
        page_num += 1
driver.close() 

# ===================== csv >> dataframe =====================

files = glob('csv\data*.csv')
 
df = pd.concat(
    (pd.read_csv(file, usecols=['縣市','鄉鎮','村里','土石流潛勢溪流編號','警戒值'],\
                 dtype={ '縣市': str, '鄉鎮':str, '村里':str, 
                        '土石流潛勢溪流編號':str,'警戒值':int})\
                 for file in files), ignore_index=True)
    
# ===================== dataframe >> 資料庫 ===================== 

con = sqlite3.connect("246.db")
cursor = con.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS Billionaire
               ("index","縣市","鄉鎮", "村里", "土石流潛勢溪流編號", "警戒值")''')  
               #建立資料表
con.commit()
 
#如果資料表存在，就寫入資料，否則建立資料表
df.to_sql('246.db', con, if_exists='replace', index=False) 

# ===================== 資料庫抓回來分析 ===================== 

df_county = pd.read_sql("SELECT 縣市 FROM '246.db'", con)

print("各縣市土石流潛勢區域數項")
print(df_county.groupby("縣市").size().sort_values(ascending=False))
print("全台土石流潛勢區域數項: " , sum(df_county.groupby("縣市").size()))

# ===================== 製圖bar1 ===================== 

Dict = {"南投縣":262,"新北市":235,"花蓮縣":170,"臺東縣":166,"宜蘭縣":150,
        "高雄市":111,"臺中市":110,"嘉義縣":87,"苗栗縣": 80,"新竹縣":77,"屏東縣":71,
        "桃園市":53,"臺北市":50,"臺南市":48,"基隆市":34,"雲林縣":13,"彰化縣":9}
df1 = pd.DataFrame(list(Dict.items()),columns=['縣市', '數量'])

col = list(range(1,18))
ind = df1['數量'].tolist()
tl = df1['縣市'].tolist() 

plt.rcParams["figure.figsize"] = (16,12)
plt.title('各縣市土石流潛勢區域數項',fontsize = 24)
plt.xlabel("縣市",size = 18)
plt.ylabel("土石流潛勢區域數項",size = 18)
plt.bar(col,ind,width = 0.5, tick_label = tl)
plt.savefig("D:/lcc/xz_python2/專題/pic/"+"246.png")
print("各縣市總圖表保存成功")
plt.close()

# ===================== 製圖bar2 ===================== 

df2 = pd.read_sql("SELECT 縣市,警戒值 FROM '246.db'", con)
for i in range(17):
    Alerted_County = tl[i]
    AlertValuecount = [0,0,0,0,0,0,0,0] 
    mask = (df2["縣市"] == Alerted_County) 
    df_AlertValue = df2[mask] 
    
    n = df_AlertValue.groupby("警戒值").size()   
    c = 300
    for j in range(8): 
        if (c in n) :
            AlertValuecount[j] += (int(n[c])) 
            c += 50
        else :
            c += 50
            
    ind2 = AlertValuecount
    col2 = list(range(1,9)) 
    tl2= [300, 350, 400, 450, 500, 550, 600, 650]
    plt.subplot(1,2,1) 
    plt.rcParams["figure.figsize"] = (16,12)
    plt.title(Alerted_County+'警戒值之數量',fontsize = 24)
    plt.ylim(0,150) 
    plt.xlabel('警戒值 單位(mm)', fontsize=16 )
    plt.ylabel('數量', fontsize=16 )
    plt.bar(col2,ind2,width =0.8, tick_label = tl2)
    
# ===================== 製圖pie ===================== 

    c = 650
    for i in range(8):    
        if ind2[7-i] == 0 :
            del ind2[7-i]
            del tl2[7-i]
            c -= 50
        else :
            c -= 50
    sizes = ind2
    labels = tl2 
    
    colors = ['lightcoral','navajowhite','lightgreen','lemonchiffon',
              'plum','paleturquoise','wheat','lightskyblue']
    plt.subplot(1,2,2)
    plt.rcParams["figure.figsize"] = (16,12)
    plt.title(Alerted_County+'各個警戒值單位(mm)之比率',fontsize = 24)
    plt.pie(sizes, labels=labels, colors=colors, autopct='%2.1f%%') 
    # 長寬比為1:1
    plt.axis('equal')
    plt.savefig("D:/lcc/xz_python2/專題/pic/"+Alerted_County+".png")
    print(Alerted_County+" 圖表保存成功")
    plt.close()