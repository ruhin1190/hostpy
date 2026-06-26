import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from bs4 import BeautifulSoup
import urllib.parse
import os
from flask import Flask
from threading import Thread

# 🔑 আপনার টেলিগ্রাম বট টোকেন
BOT_TOKEN = "8919006941:AAFlr1uPSOhWUTD7qCsPmmBvSkhovVWVFsU"
bot = telebot.TeleBot(BOT_TOKEN)

# 🌐 Render-এর জন্য ডামি ফ্ল্যাস্ক ওয়েব সার্ভার তৈরি
app = Flask('')

@app.route('/')
def home():
    return "🚀 ওস্তাদ, আপনার মেডেক্স বট রেন্ডারে চমৎকারভাবে সচল আছে!"

def run_flask():
    # Render অটোমেটিক একটি PORT প্রোভাইড করে, না থাকলে 8080 ব্যবহার করবে
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}

# 📄 তথ্য স্ক্র্যাপ করার ফাংশন
def scrape_details(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return "❌ ওস্তাদ, পেজের ডেটা লোড করা যাচ্ছে না।"
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ১. জেনেরিক পেজ হলে
        if "/generics/" in url:
            title_element = soup.select_one('h1.page-heading-1-l') or soup.select_one('h1')
            name = " ".join(title_element.text.strip().split()).replace("Generic Details", "").strip() if title_element else "Unknown Generic"
            
            ind_block = soup.select_one('#indications .ac-body') or soup.select_one('#indications')
            ind_text = " ".join(ind_block.text.strip().split()) if ind_block else "তথ্য পাওয়া যায়নি।"
            if len(ind_text) > 500: ind_text = ind_text[:500] + "..."
            
            return (
                f"🧪 *মূল জেনেরিক গ্রুপ:* {name}\n"
                f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
                f"📋 *প্রধান কার্যকারিতা (Indications):* \n_{ind_text}_\n\n"
                f"🔗 *বিস্তারিত লিংক:* {url}"
            )
            
        # ২. সাধারণ ব্র্যান্ড বা ওষুধের পেজ হলে
        else:
            title_element = soup.select_one('h1.brand-name') or soup.select_one('.brand-name') or soup.select_one('h1')
            if not title_element:
                return "❌ ওস্তাদ, ওষুধের মেইন টাইটেল খুঁজে পাওয়া যায়নি।"
                
            title = " ".join(title_element.text.strip().split())
            form_tag = soup.select_one('small.brand-dosage-form') or soup.select_one('.brand-dosage-form')
            form_type = f"({form_tag.text.strip()})" if form_tag else ""
            
            generic_element = soup.select_one('div.brand-generics a') or soup.select_one('.brand-generics') or soup.find('a', href=lambda href: href and '/generics/' in href)
            generic = " ".join(generic_element.text.strip().split()) if generic_element else "পাওয়া যায়নি"
            
            company_element = soup.select_one('div.brand-company') or soup.select_one('.brand-company') or soup.select_one('a[href*="/companies/"]')
            company = " ".join(company_element.text.strip().split()) if company_element else "পাওয়া যায়নি"
            
            price_package = soup.select_one('div.package-container') or soup.select_one('.package-container')
            price_cleaned = " ".join(price_package.text.strip().split()) if price_package else "मूल্যের তথ্য পাওয়া যায়নি"
                
            indications_header = soup.find(id='indications') or soup.find('h4', string=lambda text: text and 'Indications' in text)
            if indications_header:
                indications_block = indications_header.find_next('div', class_='ac-body') or indications_header.find_next('div')
                indications_text = " ".join(indications_block.text.strip().split()) if indications_block else "তথ্য পাওয়া যায়নি।"
                if len(indications_text) > 400: indications_text = indications_text[:400] + "..."
            else:
                indications_text = "তথ্য পাওয়া যায়নি।"

            return (
                f"💊 *ওষুধের নাম:* {title} {form_type}\n"
                f"🧪 *জেনেরিক নাম:* {generic}\n"
                f"🏢 *কোম্পানি:* {company}\n\n"
                f"💰 *মূল্য তালিকা:* \n{price_cleaned}\n\n"
                f"📋 *কার্যকারিতা (Indications):* \n_{indications_text}_\n\n"
                f"🔗 *মেডেক্স লিংক:* {url}"
            )
    except Exception as e:
        return f"❌ ডেটা স্ক্র্যাপ করতে সমস্যা হয়েছে। এরর: {e}"

# 🤖 স্টার্ট কমান্ড হ্যান্ডলার
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "🩺 *ওস্তাদের স্পেশাল সার্চ ও মেনু বট!*\n\nযেকোনো ওষুধের নাম বা নামের অংশ (যেমন: napa বা nap) টাইপ করুন। আমি ডাটাবেজ খুঁজে সব নামের একটি তালিকা দেব।")

# 🔍 টেক্সট সার্চ হ্যান্ডলার
@bot.message_handler(func=lambda message: True)
def handle_search(message):
    query = message.text.strip()
    wait_msg = bot.reply_to(message, f"🔍 '{query}' দিয়ে ডাটাবেজ স্ক্যান করা হচ্ছে...")
    
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://medex.com.bd/search?search={encoded_query}"
    
    try:
        response = requests.get(search_url, headers=HEADERS, allow_redirects=True, timeout=12)
        
        if "brands/" in response.url or "generics/" in response.url:
            bot.delete_message(message.chat.id, wait_msg.message_id)
            final_data = scrape_details(response.url)
            bot.send_message(message.chat.id, final_data, parse_mode="Markdown", disable_web_page_preview=True)
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        markup = InlineKeyboardMarkup()
        found_count = 0
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if ("/brands/" in href or "/generics/" in href) and not href.endswith('/brands') and not href.endswith('/generics') and not href.endswith('search'):
                full_url = href if href.startswith('http') else f"https://medex.com.bd{href}"
                
                button_text = " ".join(link.text.strip().split())
                if not button_text or "Read more" in button_text: 
                    continue
                
                callback_path = href.replace("https://medex.com.bd", "")
                if callback_path.startswith("/"):
                    callback_path = callback_path[1:]
                
                if len(callback_path) <= 50:
                    markup.add(InlineKeyboardButton(text=f"▪️ {button_text}", callback_data=f"med_{callback_path}"))
                    found_count += 1
                    
            if found_count >= 15:
                break

        bot.delete_message(message.chat.id, wait_msg.message_id)

        if found_count > 0:
            bot.send_message(message.chat.id, f"🎯 *'{query}' নামে এই ওষুধগুলো পাওয়া গেছে:* \n\nনিচের যেকোনো একটিতে ক্লিক করলে তার সমস্ত ডিটেইলস চলে আসবে ওস্তাদ 👇", parse_mode="Markdown", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, f"❌ ওস্তাদ, ডাটাবেজে '{query}' নামের সাথে মিল থাকা কিছু পাওয়া যায়নি।")

    except Exception as e:
        try:
            bot.delete_message(message.chat.id, wait_msg.message_id)
        except:
            pass
        bot.send_message(message.chat.id, f"⚠️ এরর হয়েছে ওস্তাদ! কারণ: {e}")

# 🔘 বাটন ক্লিক হ্যান্ডলার
@bot.callback_query_handler(func=lambda call: call.data.startswith('med_'))
def handle_button_click(call):
    path = call.data.replace("med_", "")
    target_url = f"https://medex.com.bd/{path}"
    bot.answer_callback_query(call.id, text="⏳ ডাটা প্রসেস করা হচ্ছে...")
    details_msg = scrape_details(target_url)
    bot.send_message(call.message.chat.id, details_msg, parse_mode="Markdown", disable_web_page_preview=True)

if __name__ == "__main__":
    print("🚀 ওস্তাদ, ব্যাকগ্রাউন্ডে ফ্ল্যাস্ক ওয়েব সার্ভার স্টার্ট হচ্ছে...")
    keep_alive()  # ওয়েব সার্ভার চালু করবে
    print("🤖 টেলিগ্রাম বট পোলিং শুরু হচ্ছে...")
    bot.infinity_polling()
