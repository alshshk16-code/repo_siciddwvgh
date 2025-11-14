#!/bin/bash
# ᚺᚾᛉᚲᛏ Shodan's Spear - سكريبت التثبيت السريع

echo "═══════════════════════════════════════════════════════════"
echo "  رُمْح شودان - سكريبت التثبيت"
echo "═══════════════════════════════════════════════════════════"
echo ""

# التحقق من Python
echo "[*] التحقق من Python..."
if ! command -v python3 &> /dev/null; then
    echo "[!] Python 3 غير مثبت!"
    echo "[*] جاري تثبيت Python 3..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip
fi

echo "[✓] Python 3 متوفر"
python3 --version
echo ""

# التحقق من pip
echo "[*] التحقق من pip..."
if ! command -v pip3 &> /dev/null; then
    echo "[*] جاري تثبيت pip..."
    sudo apt-get install -y python3-pip
fi

echo "[✓] pip متوفر"
echo ""

# تثبيت المكتبات
echo "[*] جاري تثبيت المكتبات المطلوبة..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "[✓] تم تثبيت جميع المكتبات بنجاح"
else
    echo "[!] حدث خطأ في تثبيت المكتبات"
    exit 1
fi

echo ""

# جعل الملف الرئيسي قابلاً للتنفيذ
echo "[*] إعداد الأذونات..."
chmod +x spear.py
echo "[✓] تم إعداد الأذونات"
echo ""

# التحقق من مفتاح Shodan API
echo "[*] التحقق من مفتاح Shodan API..."
if [ -z "$SHODAN_API_KEY" ]; then
    echo "[!] لم يتم العثور على مفتاح Shodan API في متغيرات البيئة"
    echo ""
    echo "يرجى الحصول على مفتاح API من: https://account.shodan.io/"
    echo ""
    read -p "أدخل مفتاح Shodan API الخاص بك (أو اضغط Enter للتخطي): " api_key
    
    if [ ! -z "$api_key" ]; then
        echo "export SHODAN_API_KEY=\"$api_key\"" >> ~/.bashrc
        export SHODAN_API_KEY="$api_key"
        echo "[✓] تم حفظ مفتاح API"
    else
        echo "[!] يمكنك تعيين المفتاح لاحقاً في ملف config.py"
    fi
else
    echo "[✓] تم العثور على مفتاح API"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ✓ اكتمل التثبيت بنجاح!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "لتشغيل الأداة:"
echo "  ./spear.py"
echo ""
echo "أو:"
echo "  python3 spear.py"
echo ""
echo "═══════════════════════════════════════════════════════════"
