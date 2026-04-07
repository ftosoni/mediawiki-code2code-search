import json
import os

i18n_dir = "frontend/i18n"
translations = {
    "as": {"score": "মেচিং স্কোৰ", "msg": "এটা কোড স্নিয়েট লিখক..."},
    "bn": {"score": "মানানসই স্কোর", "msg": "একটি কোড স্নিপেট লিখুন..."},
    "en": {"score": "MATCHING SCORE", "msg": "Write a code snippet and I'll find similar ones..."},
    "fr": {"score": "SCORE", "msg": "Écrivez un extrait de code..."},
    "gu": {"score": "મેચિંગ સ્કોર", "msg": "એક કોડ સ્નિપેટ લખો..."},
    "hi": {"score": "मिलान स्कोर", "msg": "एक कोड स्निपेट लिखें..."},
    "it": {"score": "MATCHING SCORE", "msg": "Scrivi uno snippet di codice e ne troverò di simili..."},
    "kn": {"score": "ಸ್ಕೋರ್", "msg": "ಕೋಡ್ ಸ್ನಿಪ್ಪೆಟ್ ಬರೆಯಿರಿ..."},
    "mai": {"score": "मैचिंग स्कोर", "msg": "एकटा कोड स्निपेट लिखू..."},
    "ml": {"score": "മാച്ചിംഗ് സ്കോർ", "msg": "ഒരു കോഡ് സ്‌നിപ്പറ്റ് എഴുതുക..."},
    "mr": {"score": "मॅचिंग स्कोर", "msg": "एक कोड स्निपेट लिहा..."},
    "or": {"score": "ମେଳକ ସ୍କୋର", "msg": "ଏକ କୋଡ୍ ସ୍ନିପେଟ୍ ଲେଖନ୍ତୁ..."},
    "pa": {"score": "ਮੇਲ ਖਾਂਦਾ ਸਕੋਰ", "msg": "ਇੱਕ ਕੋਡ ਸਨਿੱਪਟ ਲਿਖੋ..."},
    "sat": {"score": "ᱢᱮᱞ ᱠᱷᱟᱱᱟ ᱥᱠᱳᱨ", "msg": "ᱢᱤᱫᱴᱟᱹᱝ ᱠᱳᱰ ᱥᱱᱤᱯᱮᱴ ᱚᱞ ᱢᱮ..."},
    "ta": {"score": "பொருந்தும் மதிப்பெண்", "msg": "ஒரு குறியீடு துணுக்கை எழுதுங்கள்..."},
    "te": {"score": "పోలిక స్కోరు", "msg": "కోడ్ స్నిప్పెట్‌ను రాయండి..."},
    "ur": {"score": "میچنگ سکور", "msg": "ایک کوڈ اسنیپٹ لکھیں..."}
}

for filename in os.listdir(i18n_dir):
    if filename.endswith(".json"):
        lang = filename.split(".")[0]
        filepath = os.path.join(i18n_dir, filename)
        
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Update labels to match your request
        if lang in translations:
            data["placeholder"] = translations[lang]["msg"]
            data["recall_score"] = translations[lang]["score"]
            # Ensure footer keys exist
            if "view_source" not in data: data["view_source"] = "View source"
            if "view_swhid" not in data: data["view_swhid"] = "View SWHID"
        else:
            data["placeholder"] = "Write a code snippet..."
            data["recall_score"] = "MATCHING SCORE"
            
        # Clean up old tags
        if "rerank_score" in data: del data["rerank_score"]
        if "last_updated" in data: del data["last_updated"]
            
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        print(f"Updated {filename}")
