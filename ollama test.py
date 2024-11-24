# 導入所需模組
import discord
import ollama
import requests
import gzip
import io
import json
import pandas as pd
import re

# 設定 Discord bot 的 intents
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Google Drive 下載連結轉換函數
def get_google_drive_download_url(drive_url):
    file_id = drive_url.split('/')[-2]
    return f'https://drive.google.com/uc?id={file_id}&export=download'

# 載入路線數據
route_info_url = get_google_drive_download_url('https://drive.google.com/file/d/1KYSoPxrKPlSm6uL-o3K2LUhNmEqkuOAt/view?usp=drive_link')
route_info = pd.read_csv(route_info_url)

stop_id_url = get_google_drive_download_url('https://drive.google.com/file/d/1F1mptcRJ1pNdFKQ0jsOTnj7EoS6nrjOF/view?usp=drive_link')
stop_id_data = pd.read_csv(stop_id_url)

stop_info_url = get_google_drive_download_url('https://drive.google.com/file/d/1vieH8N1ebHEfNKaDv4TG9yULr_w7_Ud-/view?usp=sharing')
stop_info = pd.read_csv(stop_info_url)

# 讀取 GetBusEvent 數據
def get_bus_event_data():
    bus_event_url = "https://tcgbusfs.blob.core.windows.net/blobbus/GetBusEvent.gz"
    response_bus = requests.get(bus_event_url)
    if response_bus.status_code == 200:
        with gzip.GzipFile(fileobj=io.BytesIO(response_bus.content)) as f:
            data = f.read()
        return json.loads(data)
    return None

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')  # 顯示機器人的名稱，確認機器人已經登入

    # 獲取機器人加入的所有伺服器
    for guild in client.guilds:
        print(f"已加入伺服器: {guild.name}")
        
        # 遍歷伺服器中的所有頻道，選擇第一個文字頻道
        for channel in guild.text_channels:
            # 確保是文字頻道
            if isinstance(channel, discord.TextChannel):
                await channel.send("你好我是騙人公車模擬器!\n\n輸入 %公車 或者 %路線 即可獲得公車最新訊息!\n\n或者用%chat跟我講話喔!")  # 在這裡輸入你想發送的訊息
                return  # 只發送一次，之後停止

def read_prompt_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            prompt = file.read().strip()
            print(f"Prompt read successfully: {prompt[:100]}...")  # 只印出前 100 字以防太長
            return prompt
    except Exception as e:
        print(f"Failed to read prompt from file: {e}")
        return ""

# 直接在 on_message 中處理消息
@client.event
async def on_message(message):
    # 如果訊息是來自機器人自己，則忽略
    if message.author == client.user:
        return

    if message.content.startswith("%chat"):
        await message.channel.send("我想想")

        try:
            # 讀取檔案中的 prompt
            prompt = read_prompt_from_file("\桐谷和人檔案.txt") #可自行更改
            user_input = message.content[len("%chat"):].strip()
            full_prompt = f"{prompt}\n使用者說：{user_input}"
            
            # 發送請求給 ollama
            response = ollama.chat(model="llama2-chinese:13b", messages=[{"role": "user", "content": full_prompt}])

            # 確認回應是否有內容
            if 'message' in response and 'content' in response['message']:
                content = response['message']['content']
                if content.strip():  # 檢查內容是否非空
                    await message.channel.send(content)
                else:
                    await message.channel.send("無法獲得有效的回應。")
            else:
                await message.channel.send("無法獲得有效的回應。")

        except Exception as e:
            await message.channel.send(f"發生錯誤: {e}")

    # 查詢公車路線
    elif any(keyword in message.content for keyword in ["%公車", "%路線"]):
        await message.channel.send("請輸入路線名稱的關鍵字 (例如: 234)")  # 提示用戶輸入路線名稱

        try:
            # 假設這裡的 '234' 是示例，改為使用用戶的實際輸入
            user_input_route = message.content[len("%路線"):].strip()
            matched_routes = route_info[route_info['中文名稱'].str.contains(user_input_route)]  # 使用用戶輸入的路線名稱關鍵字

            if matched_routes.empty:
                await message.channel.send(f"未找到符合的路線名: {user_input_route}，請重新輸入有效的路線名稱。")
                return  
            else:
                await message.channel.send(f"成功找到路線資料！")

                bus_event_data = get_bus_event_data()
                if bus_event_data:

                    # 確保 bus_event_data 是列表或字典
                    if isinstance(bus_event_data, list):
                        go_back_data = {}

                        for event in bus_event_data:
                            if isinstance(event, dict):  # 確保每個 event 是字典
                                go_back = event.get('GoBack', '未知')  # 使用 get() 來避免 KeyError
                                stop_name = event.get('StopName', '未知站名')
                                remaining_stops = event.get('RemainingStops', '未知')

                                if go_back not in go_back_data:
                                    go_back_data[go_back] = []

                                go_back_data[go_back].append(f"目前車輛停在 {stop_name}, 距離目標站剩餘站數: {remaining_stops}")

                        # 將每個 GoBack 狀態的資料發送到 Discord
                        for go_back, data in go_back_data.items():
                            await message.channel.send(f"GoBack_{go_back} 的車輛資料：")
                            for line in data:
                                await message.channel.send(line)

                else:
                    await message.channel.send("無法獲取公車事件資料。")
            
        except Exception as e:
            await message.channel.send(f"發生錯誤: {e}")

        # 等待用戶輸入路線名稱
        def check(msg):
            return msg.author == message.author and msg.channel == message.channel

        route_input_message = await client.wait_for("message", check=check)
        route_input = route_input_message.content.strip()

        # 查找符合關鍵字的路線
        # 當用戶輸入路線名稱後，開始查找並回應結果
        matched_routes = route_info[route_info['中文名稱'].str.contains(route_input) | 
                                    route_info['英文名稱'].str.contains(route_input)]

        if not matched_routes.empty:
            found_routes = matched_routes['路線代碼'].astype(str).tolist()

            await message.channel.send("請輸入站名的關鍵字 (中文):")
            stop_input_message = await client.wait_for("message", check=check)
            stop_input = stop_input_message.content.strip()

            for route_id in found_routes:
                route_stops = stop_info[stop_info['RouteID'] == int(route_id)]
                matched_stop = route_stops[route_stops['NameZh'].str.contains(stop_input)]
                
                if not matched_stop.empty:
                    stop_info_by_goback = {'GoBack_0': [], 'GoBack_1': []}
                    for idx, row in matched_stop.iterrows():
                        seq_no = row['SeqNo']
                        go_back = row['GoBack']
                        stop_name_zh = row['NameZh']
                        stop_info_by_goback[f'GoBack_{go_back}'].append(seq_no)

                    path_detail_url = "https://tcgbusfs.blob.core.windows.net/blobbus/GetPathDetail.gz"
                    response_path = requests.get(path_detail_url)

                    if response_path.status_code == 200:
                        with gzip.GzipFile(fileobj=io.BytesIO(response_path.content)) as f:
                            path_data = f.read()
                        path_detail_data = json.loads(path_data)
                        bus_event_data = get_bus_event_data()

                        found_stops = {'GoBack_0': [], 'GoBack_1': []}
                        for entry in bus_event_data['BusInfo']:
                            route_id_from_stop = entry.get('RouteID')
                            if str(route_id_from_stop) in found_routes:
                                stop_id = entry.get('StopID')
                                stop_name_row = stop_info[stop_info['Id'] == int(stop_id)]
                                if not stop_name_row.empty:
                                    stop_name = stop_name_row['NameZh'].values[0]
                                    sub_route_id = route_info[route_info['路線代碼'] == int(route_id)]['所屬附屬路線 ID'].values[0]
                                    path_detail = [
                                        b for b in path_detail_data['BusInfo']
                                        if b['pathAttributeId'] == int(sub_route_id)
                                    ]
                                    current_stop_seq = next(
                                        (b['sequenceNo'] for b in path_detail if b['stopId'] == int(stop_id)), None
                                    )
                                    go_back_val = entry.get('GoBack', '0')
                                    found_stops[f'GoBack_{go_back_val}'].append({
                                        'StopID': stop_id,
                                        'Stop Name': stop_name,
                                        'RouteID': route_id_from_stop,
                                        '車輛詳細資料': entry,
                                        '站序': current_stop_seq
                                    })
                        # 根據 GoBack 值分別處理
                        for go_back_value in ['GoBack_0', 'GoBack_1']:
                            # 確保 stop_info_by_goback 中有這個 GoBack 值的數據
                            if go_back_value in stop_info_by_goback and stop_info_by_goback[go_back_value]:
                                target_seq = stop_info_by_goback[go_back_value][0]
                                #await message.channel.send(f"\n{go_back_value} 的車輛資料：")

                                # 根據 GoBack 值篩選符合條件的班車
                                if go_back_value == 'GoBack_0':
                                    eligible_stops = [
                                        stop for stop in found_stops[go_back_value]
                                        if stop['站序'] < target_seq  # GoBack 0 的站序必須小於 target_seq
                                    ]
                                    # 從 route_info 中取得訖站中文名稱，增加檢查
                                    end_station_name_row = route_info[route_info['路線代碼'] == int(route_id)]
                                    if not end_station_name_row.empty:
                                        end_station_name = end_station_name_row['訖站中文名稱'].values[0]
                                        await message.channel.send(f"往 {end_station_name} 的車輛資料：")
                                    else:
                                        await message.channel.send(f"路線 {route_input} 還沒有發車!")
                                else:  # GoBack_1
                                    eligible_stops = [
                                        stop for stop in found_stops[go_back_value]
                                        if stop['站序'] < target_seq  # GoBack 1 的站序必須大於 target_seq
                                    ]
                                    # 從 route_info 中取得起站中文名稱，增加檢查
                                    start_station_name_row = route_info[route_info['路線代碼'] == int(route_id)]
                                    if not start_station_name_row.empty:
                                        start_station_name = start_station_name_row['起站中文名稱'].values[0]
                                        await message.channel.send(f"往 {start_station_name} 的車輛資料：")
                                    else:
                                        await message.channel.send(f"路線 {route_input} 還沒有發車!")

                                # 根據與 target_seq 的絕對差值排序，取最接近的 3 班車
                                sorted_stops = sorted(
                                    eligible_stops,
                                    key=lambda x: abs(x['站序'] - target_seq)
                                )

                                # 用來檢查已經列印過的車站名稱
                                closest_stops = sorted_stops[:3]
                                printed_stops = set()

                                for stop in closest_stops:
                                    stop_name = stop['Stop Name']
                                    stop_seq = stop['站序']
                                    remaining_stops = abs(stop_seq - target_seq)

                                    if stop_name not in printed_stops:
                                        await message.channel.send(f"目前車輛停在 {stop_name}, 距離目標站剩餘站數: {remaining_stops}")
                                        printed_stops.add(stop_name)
                            else:
                                await message.channel.send(f"往{start_station_name} 的車輛尚未發車")


# 將您的 Discord Bot Token 放在此處 
client.run("")
