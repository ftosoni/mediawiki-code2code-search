import json
import os

i18n_dir = "frontend/i18n"
translations = {
    "as": {"score": "ম্যাচিং স্কোৰ", "msg": "এটা কোড স্নিয়েট লিখক আৰু মই তেনেধৰণৰ আন কিছুমান বিচাৰি উলিয়াম...", "source": "সোর্স দেখুন", "swhid": "SWHID দেখুন", "created": "দ্বাৰা নিৰ্মিত:", "licence": "লাইচেন্স:"},
    "bn": {"score": "মানানসই স্কোর", "msg": "একটি কোড স্নিপেট লিখুন এবং আমি একই ধরণের কোড খুঁজে দেব...", "source": "সোর্স দেখুন", "swhid": "SWHID দেখুন", "created": "তৈরি করেছেন:", "licence": "লাইসেন্স:"},
    "en": {"score": "MATCHING SCORE", "msg": "Write a code snippet and I'll find similar ones...", "source": "View source", "swhid": "View SWHID", "created": "Created by:", "licence": "Licence:"},
    "fr": {"score": "SCORE DE CORRESPONDANCE", "msg": "Écrivez un extrait de code et j'en trouverai des similaires...", "source": "Voir la source", "swhid": "Voir SWHID", "created": "Créé par :", "licence": "Licence :"},
    "gu": {"score": "મેચિંગ સ્કોર", "msg": "એક કોડ સ્નિપેટ લખો અને હું તેવા જ અન્ય શોધીશ...", "source": "સ્ત્રોત જુઓ", "swhid": "SWHID જુઓ", "created": "દ્વારા બનાવવામાં આવ્યું:", "licence": "લાયસન્સ:"},
    "hi": {"score": "मिलान स्कोर", "msg": "एक कोड स्निपेट लिखें और मैं समान ढूंढूंगा...", "source": "स्रोत देखें", "swhid": "SWHID देखें", "created": "द्वारा बनाया गया:", "licence": "लाइसेंस:"},
    "it": {"score": "PUNTEGGIO DI CORRISPONDENZA", "msg": "Scrivi uno snippet di codice e ne troverò di simili...", "source": "Vedi sorgente", "swhid": "Vedi SWHID", "created": "Creato da:", "licence": "Licenza:"},
    "kn": {"score": "ಹೊಂದಾಣಿಕೆಯ ಸ್ಕೋರ್", "msg": "ಕೋಡ್ ಸ್ನಿಪ್ಪೆಟ್ ಬರೆಯಿರಿ ಮತ್ತು ನಾನು ಅಂತಹುದೇ ಸ್ನಿಪ್ಪೆಟ್‌ಗಳನ್ನು ಹುಡುಕುತ್ತೇನೆ...", "source": "ಮೂಲವನ್ನು ನೋಡಿ", "swhid": "SWHID ನೋಡಿ", "created": "ಇವರಿಂದ ರಚಿಸಲಾಗಿದೆ:", "licence": "ಪರವಾನಗಿ:"},
    "mai": {"score": "मैचिंग स्कोर", "msg": "एकटा कोड स्निपेट लिखू आ हम ओहिना टाइप के आर ढूंढब...", "source": "स्रोत देखू", "swhid": "SWHID देखू", "created": "द्वारा निर्मित:", "licence": "लाइसेंस:"},
    "ml": {"score": "മാച്ചിംഗ് സ്കോർ", "msg": "ഒരു കോഡ് സ്‌നിപ്പറ്റ് എഴുതുക, അത്തരത്തിലുള്ള മറ്റൊന്ന് ഞാൻ കണ്ടെത്തും...", "source": "സോഴ്സ് കാണുക", "swhid": "SWHID കാണുക", "created": "നിർമ്മിച്ചത്:", "licence": "ലൈസൻസ്:"},
    "mr": {"score": "मॅचिंग स्कोर", "msg": "एक कोड स्निपेट लिहा आणि मी त्यासारखेच शोधून देईन...", "source": "स्रोत पहा", "swhid": "SWHID पहा", "created": "यांनी बनवले:", "licence": "परवाना:"},
    "or": {"score": "ମେଳକ ସ୍କୋର", "msg": "ଏକ କୋଡ୍ ସ୍ନିପେଟ୍ ଲେଖନ୍ତୁ ଏବଂ ମୁଁ ସମାନ କୋଡ୍ ସ୍ନିପେଟ୍ ଗୁଡ଼ିକ ଖୋଜିବି...", "source": "ସୋର୍ସ ଦେଖନ୍ତୁ", "swhid": "SWHID ଦେଖନ୍ତୁ", "created": "ଦ୍ୱାରା ନିର୍ମିତ:", "licence": "ଲାଇସେନ୍ସ:"},
    "pa": {"score": "ਮੇਲ ਖਾਂਦਾ ਸਕੋਰ", "msg": "ਇੱਕ ਕੋਡ ਸਨਿੱਪਟ ਲਿਖੋ ਅਤੇ ਮੈਂ ਉਸ ਵਰਗੇ ਹੋਰ ਲਭਾਂਗਾ...", "source": "ਸਰੋਤ ਦੇਖੋ", "swhid": "SWHID ਦੇਖੋ", "created": "ਦੁਆਰਾ ਬਣਾਇਆ ਗਿਆ:", "licence": "ਲਾਇਸੈਂਸ:"},
    "sat": {"score": "ᱢᱮᱞ ᱠᱷᱟᱱᱟ ᱥᱠᱳᱨ", "msg": "ᱢᱤᱫᱴᱟᱹᱝ ᱠᱳᱰ ᱥᱱᱤᱯᱮᱴ ᱚᱞ ᱢᱮ ᱟᱨ ᱤᱧ ᱚᱱᱟ ᱞᱮᱠᱟᱱᱟᱜ ᱮᱴᱟᱜᱟᱜ ᱤᱧ ᱧᱟਮᱟ...", "source": "ᱥᱳᱨᱥ ᱧᱮᱞ ᱢᱮ", "swhid": "SWHID ᱧᱮᱞ ᱢᱮ", "created": "ᱵᱮᱱᱟᱣᱤᱡ:", "licence": "ᱞᱟᱭᱥᱮᱱᱥ:"},
    "ta": {"score": "பொருந்தும் மதிப்பெண்", "msg": "ஒரு குறியீடு துணுக்கை எழுதுங்கள், நான் அதைப் போன்றவற்றைத் தேடுவேன்...", "source": "மூலத்தைப் பார்க்கவும்", "swhid": "SWHID ஐப் பார்க்கவும்", "created": "உருவாக்கியவர்:", "licence": "உரிமம்:"},
    "te": {"score": "పోలిక స్కోరు", "msg": "కోడ్ స్నిప్పెట్‌ను రాయండి మరియు నేను సారూప్యమైన వాటిని కనుగొంటాను...", "source": "మూలాన్ని చూడండి", "swhid": "SWHID చూడండి", "created": "రూపొందించినవారు:", "licence": "లైసెన్స్:"},
    "ur": {"score": "میچنگ سکور", "msg": "ایک کوڈ اسنیپٹ لکھیں اور میں اس جیسے دوسرے تلاش کروں گا...", "source": "ماخذ دیکھیں", "swhid": "SWHID دیکھیں", "created": "تخلیق کار:", "licence": "لائسنس:"}
}

for filename in os.listdir(i18n_dir):
    if filename.endswith(".json"):
        lang = filename.split(".")[0]
        filepath = os.path.join(i18n_dir, filename)
        
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Update logic
        if lang in translations:
            data["placeholder"] = translations[lang]["msg"]
            data["recall_score"] = translations[lang]["score"]
            data["view_source"] = translations[lang]["source"]
            data["view_swhid"] = translations[lang]["swhid"]
            data["created_by"] = translations[lang]["created"]
            data["licence"] = translations[lang]["licence"]
        else:
            # Fallback
            data["placeholder"] = "Write a code snippet and I'll find similar ones..."
            data["recall_score"] = "MATCHING SCORE"
            data["view_source"] = "View source"
            data["view_swhid"] = "View SWHID"
            data["created_by"] = "Created by:"
            data["licence"] = "Licence:"
            
        # Remove old keys
        if "rerank_score" in data:
            del data["rerank_score"]
        if "last_updated" in data:
            del data["last_updated"]
            
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        print(f"Updated {filename}")
