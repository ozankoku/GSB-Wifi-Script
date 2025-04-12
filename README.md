# KYK Wi-Fi Otomatik Giriş & Kota Kontrol Scripti v1.0.0

## **⚠️ Uyarı ⚠️**

**Bu script, web otomasyon tekniklerini göstermek amacıyla yalnızca eğitim amaçlı sunulmaktadır.** Python kullanarak bir web portalıyla programatik olarak nasıl etkileşim kurulacağını örneklendirir.

**Bu script'i KESİNLİKLE GSB/KYK Wi-Fi ağını veya hizmetlerini istismar etmek, engellemek veya bozmak için KULLANMAYIN.** Bilgisayar sistemlerine yetkisiz erişim veya müdahale yasa dışı ve etik dışıdır. Geliştiriciler, bu script'in yanlış kullanımından veya neden olduğu herhangi bir zarardan sorumlu tutulamazlar. Kullanım riski ve sorumluluğu tamamen size aittir. Kullanımınızın GSB/KYK hizmet şartlarına uygun olduğundan emin olun.

---

*Bu proje Gençlik ve Spor Bakanlığı (GSB) veya Kredi ve Yurtlar Kurumu (KYK) ile ilişkili değildir, onlar tarafından onaylanmamış veya desteklenmemiştir.*

---

## Genel Bakış

Bu proje, Gençlik ve Spor Bakanlığı (GSB) Kredi ve Yurtlar Kurumu (KYK) yurtlarında kullanılan Wi-Fi ağına (`wifi.gsb.gov.tr`) otomatik olarak giriş yapmayı, kalan internet kotasını sorgulamayı ve oturumu yönetmeyi sağlayan bir Python script'idir (`v1.0.0`, dosya adı: `kyk_wifi_helper.py`).

Zaman zaman güvenilmez veya kullanımı zor olabilen KYK Wi-Fi portalı ile daha stabil ve otomatik bir şekilde etkileşim kurmayı hedefler. Script'in amacı yalnızca giriş yapmayı ve oturum yönetimini kolaylaştırmaktır; herhangi bir kısıtlamayı aşmak veya ağı kötüye kullanmak gibi bir niyeti yoktur.

## Özellikler

*   **Otomatik Giriş:** TC Kimlik Numarası (Kullanıcı Adı) ve şifreniz ile KYK Wi-Fi portalına otomatik olarak bağlanır.
*   **Kota Sorgulama:** Mevcut internet kotanızın ne kadar kaldığını (MB cinsinden) gösterir.
*   **Oturumu Açık Tutma (Keep-Alive):**
    *   **Normal Mod:** Belirli aralıklarla (varsayılan 10 dakika) kota kontrolü yaparak Wi-Fi oturumunuzun zaman aşımı nedeniyle otomatik olarak kapanmasını engeller. Güncel kota bilgisi de ekranda gösterilir.
    *   **Hızlı Mod:** Daha sık aralıklarla (varsayılan 10 saniye) kontrol yaparak oturumu aktif tutar (performans için bu modda kota bilgisi gösterilmez).
*   **Güvenli Bilgi Saklama:** Giriş bilgilerinizi (TC Kimlik No ve şifre) isteğe bağlı olarak, programın bulunduğu dizinde yerel olarak oluşturulan `.env` adlı bir dosyada güvenli bir şekilde saklar. Bu, sonraki çalıştırmalarda bilgilerin tekrar girilmesini gerektirmez.
*   **İnteraktif Menü:** Başarılı giriş sonrası kullanıcıya çeşitli seçenekler sunar: Kalan Kotayı Göster, Oturumu Açık Tut (Normal/Hızlı), Giriş Bilgilerini Değiştir, Oturumu Kapatıp Çık, Oturumu Açık Bırakıp Çık.
*   **Varsayılan Seçenek:** Menüde hiçbir seçim yapmadan `Enter` tuşuna basıldığında varsayılan olarak "Kalan Kotayı Göster" (Seçenek 1) seçeneği çalıştırılır.
*   **Giriş Bilgilerini Değiştirme:** Program çalışırken menü aracılığıyla yeni TC Kimlik Numarası ve şifre girmenize olanak tanır ve bu bilgileri yerel `.env` dosyasına kaydeder.
*   **Oturum Takibi:** Aktif Wi-Fi oturumunun kimliğini (`JSESSIONID`) geçici bir yerel dosyada (`session_info.txt`) saklayarak çıkış işlemini ve oturum yönetimini kolaylaştırır.
*   **Detaylı Loglama:** Tüm işlemleri (giriş denemeleri, başarı/hata durumları, kota sorguları, çıkışlar vb.) `kyk_login.log` adlı yerel bir dosyaya zaman damgasıyla kaydeder. Sorun giderme için oldukça kullanışlıdır.
*   **İlk Çalıştırma Yardımcısı:** Program ilk kez çalıştırıldığında, bu `README.md` dosyasını açmayı teklif eder ve giriş bilgilerini kaydetme seçeneği sunar.
*   **Graceful Shutdown:** `Ctrl+C` tuş kombinasyonu kullanıldığında programı düzgün bir şekilde sonlandırmaya çalışır. Mümkünse, açık olan Wi-Fi oturumunu kapatarak çıkar. Keep-Alive modlarından ana menüye dönmek için de `Ctrl+C` kullanılır.
*   **Renkli Konsol Çıktısı:** Daha iyi okunabilirlik için (eğer yüklüyse) `colorama` kütüphanesi kullanılarak konsol çıktıları renklendirilir.

## Repository Yapısı

*   `kyk_wifi_helper.py`: Ana script dosyası.
*   `requirements.txt`: Gerekli Python kütüphanelerini listeleyen dosya.
*   `README.md`: Bu bilgilendirme dosyası (Türkçe/İngilizce).
*   `app_icon.ico`: Uygulama ikonu (.exe derlemesi için).
*   `.env` (Oluşturulursa): Kullanıcı adı ve şifrenin yerel olarak saklandığı dosya.
*   `session_info.txt` (Oluşturulursa): Aktif oturum bilgisini saklayan geçici yerel dosya.
*   `kyk_login.log` (Oluşturulursa): İşlem kayıtlarının tutulduğu yerel log dosyası.
*   `.ilk_calistirma_tamam` (Oluşturulursa): İlk çalıştırma yardımcısının tekrar gösterilmesini engelleyen yerel işaretçi dosya (gizli olabilir).
*   `build/`: PyInstaller derleme işlemi sırasında oluşturulan dosyalar.
*   `dist/`: Derleme sonucu oluşan dağıtılabilir `.exe` dosyasının bulunduğu klasör.

## Gereksinimler

*   **Python:** Python 3.x sürümü kurulu olmalıdır.
*   **Kütüphaneler:** Aşağıdaki Python kütüphanelerinin kurulu olması gerekmektedir:
    *   `requests` (HTTP istekleri için)
    *   `python-dotenv` (`.env` dosyasını yönetmek için)
    *   `beautifulsoup4` (HTML/XML ayrıştırmak için)
    *   `lxml` (önerilir, `beautifulsoup4` için daha hızlı bir ayrıştırıcıdır)
    *   `colorama` (isteğe bağlı, renkli konsol çıktıları için)

## Kurulum (Python Script için)

1.  **Projeyi Edinin:** Proje dosyalarını bilgisayarınıza indirin veya `git clone` ile klonlayın.
2.  **Kütüphaneleri Yükleyin:** Proje dizininde bir terminal veya komut istemcisi açın ve `requirements.txt` kullanarak gerekli kütüphaneleri yükleyin:
    ```bash
    pip install -r requirements.txt
    ```
    Alternatif olarak, tek tek yükleyebilirsiniz:
    ```bash
    pip install requests python-dotenv beautifulsoup4 lxml colorama
    ```

## Çalıştırılabilir Dosyayı İndirme (.exe)

Eğer bilgisayarınıza Python kurmak veya script'i kaynak kodundan kendiniz derlemek istemiyorsanız, Windows için önceden derlenmiş bir sürümü kullanabilirsiniz.

*   Bu repository'nin **[Releases (Sürümler)](https://github.com/ozankoku/GSB-Wifi-Script/releases)** sayfasına gidin.
*   `v1.0.0` (veya en güncel) etiketli sürümü bulun ve "Assets" (Varlıklar) başlığı altında listelenen `.exe` dosyasını indirin.
*   İndirdiğiniz `.exe` dosyasını herhangi bir kurulum yapmadan doğrudan çalıştırabilirsiniz.

## Çalıştırılabilir Dosya Oluşturma (.exe)

Script'i Python kurulu olmayan Windows sistemlerde çalıştırmak veya kolayca paylaşmak için PyInstaller kullanarak kendi `.exe` dosyanızı oluşturabilirsiniz.

1.  **PyInstaller Kurulumu:** Eğer kurulu değilse, yükleyin:
    ```bash
    pip install pyinstaller
    ```
2.  **`.exe` Oluşturma:** Terminalde proje ana dizinindeyken aşağıdaki komutu çalıştırın:
    ```bash
    pyinstaller --onefile --windowed --icon=app_icon.ico kyk_wifi_helper.py
    ```
    *   `--onefile`: Tüm bağımlılıkları tek bir `.exe` dosyasında toplar.
    *   `--windowed`: Arka planda açılan komut istemi penceresini gizler (isteğe bağlı).
    *   `--icon=app_icon.ico`: Uygulama için özel ikon belirler.

3.  **Sonuç:** Başarılı bir derleme işleminden sonra, oluşturulan `.exe` dosyası projenizdeki `dist` klasörünün içinde bulunacaktır.

## Kullanım

**Önemli:** Script'in başarılı bir şekilde giriş yapabilmesi için cihazınızın KYK Wi-Fi ağına bağlı olması **ve** henüz web portalı üzerinden manuel olarak giriş yapmamış olmanız gerekmektedir.

1.  **Çalıştırma:**
    *   **`.exe` Dosyası ile:** İndirdiğiniz veya derlediğiniz `.exe` dosyasına çift tıklayarak çalıştırın.
    *   **Python Script Olarak:** Proje dizininde bir terminal açın ve şu komutu girin:
        ```bash
        python kyk_wifi_helper.py
        ```

2.  **İlk Çalıştırma:**
    *   Eğer `.env` dosyası bulunmuyorsa, script sizden TC Kimlik Numaranızı (Kullanıcı Adı) ve KYK Wi-Fi şifrenizi (Parola) girmenizi isteyecektir.
    *   Bu bilgileri ileride kullanmak üzere yerel `.env` dosyasına kaydetmek isteyip istemediğiniz sorulacaktır. 'e' veya 'y' yanıtı verirseniz, bilgiler kaydedilir.
    *   Ayrıca, bilgilendirme amaçlı bu `README.md` dosyasını açmak isteyip istemediğiniz sorulabilir.

3.  **Menü Navigasyonu:**
    *   Başarılı girişin ardından ekranda ana menü belirecektir.
    *   Yapmak istediğiniz işleme karşılık gelen sayıyı (1, 2, 3, 4, 5, 6) girip `Enter` tuşuna basın.
    *   Hiçbir giriş yapmadan `Enter` tuşuna basarsanız, varsayılan olarak '1' (Kalan Kotayı Göster) seçeneği çalıştırılır.
    *   "Oturumu Açık Tut" (Normal veya Hızlı) modlarında çalışırken ana menüye geri dönmek için `Ctrl+C` tuş kombinasyonunu kullanın.
    *   Programı tamamen kapatmak için menüden ilgili çıkış seçeneğini (5 veya 6) seçin veya herhangi bir zamanda `Ctrl+C`'ye basın (ikinci `Ctrl+C` genellikle programı sonlandırır ve oturumu kapatmaya çalışır).

## Yapılandırma

*   **`.env` Dosyası:** Script, ilk çalıştırmada onayınızla kullanıcı adı ve şifreyi yerel olarak bu dosyaya kaydeder. Dosya formatı şöyledir:
    ```dotenv
    KYK_USERNAME=TC_KIMLIK_NUMARANIZ
    KYK_PASSWORD=SIFRENIZ
    ```
    Bu dosyayı manuel olarak da oluşturabilir veya düzenleyebilirsiniz. Güvenlik için bu dosyanın içeriğini kimseyle paylaşmayın.
    *   `.env` dosyasını silerseniz, program bir sonraki çalıştırmada tekrar giriş bilgilerini soracaktır.

## Loglama

*   Script, tüm önemli aktiviteleri ve olası hataları `kyk_login.log` adlı yerel bir dosyaya kaydeder. Herhangi bir sorunla karşılaşırsanız, sorunun kaynağını anlamak için öncelikle bu dosyayı kontrol edin.

## Önemli Notlar

*   **Güvenlik:** `.env` dosyası hassas giriş bilgilerinizi içerir ve sadece sizin bilgisayarınızda yerel olarak saklanır. Bu dosyanın bulunduğu klasörü güvende tutun ve içeriğini başkalarıyla paylaşmaktan kaçının.
*   **Portal Değişiklikleri:** KYK Wi-Fi portalının web arayüzünde (HTML yapısı, form alanları, URL'ler vb.) değişiklikler olması durumunda, script'in bazı işlevleri (özellikle giriş, kota sorgulama) çalışmayabilir. Bu gibi durumlarda scriptin güncellenmesi gerekebilir. Log dosyasındaki (`kyk_login.log`) hatalar bu konuda ipucu verebilir.
*   **Ağ Bağlantısı:** Script'in çalışabilmesi için cihazınızın aktif olarak KYK Wi-Fi ağına bağlı olması gerekmektedir. Giriş yapmadan önce bağlantınızı kontrol edin.
*   **Colorama:** Renkli konsol çıktıları için `colorama` kütüphanesi kullanılır. Eğer bu kütüphane sisteminizde yüklü değilse, script çalışmaya devam eder ancak çıktılar renksiz olur.
*   **Sorumlu Kullanım:** Lütfen script'i GSB/KYK ağ kullanım politikalarına ve hizmet şartlarına uygun şekilde, ağa aşırı yük bindirmeden sorumlu bir şekilde kullanın.

## Sorun Giderme

*   **Giriş Başarısız:**
    *   Öncelikle TC Kimlik Numaranızın ve şifrenizin doğru olduğundan emin olun.
    *   Eğer `.env` dosyası kullanıyorsanız, dosyanın içeriğini (`KYK_USERNAME=...`, `KYK_PASSWORD=...` formatında) kontrol edin. Emin değilseniz, `.env` dosyasını silip script'i yeniden başlatarak bilgileri tekrar girmeyi deneyin.
    *   `kyk_login.log` dosyasını açın ve "CREDENTIAL_ERROR", "Hatali kullanici adi veya sifre" gibi hata mesajları arayın.
*   **Kota Gösterilemiyor / Oturum Açık Tutma Çalışmıyor:**
    *   `kyk_login.log` dosyasını kontrol edin. "ViewState", "AJAX", "SESSION_EXPIRED" veya HTML ayrıştırma ile ilgili hatalar var mı bakın.
    *   Bu durum, KYK portalında geçici bir sorun olduğunu veya portalın web yapısının değiştiğini gösterebilir (bkz. Önemli Notlar). Script güncellemesi gerekebilir.
    *   "SESSION_EXPIRED" hatası alıyorsanız, script genellikle otomatik olarak yeniden giriş yapmayı deneyecektir. Tekrarlıyorsa başka bir sorun olabilir.
*   **Ağ Hataları (`ConnectionError`, `Timeout` vb.):**
    *   Cihazınızın KYK Wi-Fi ağına düzgün bağlandığından ve internet erişimi olduğundan emin olun (örneğin, başka bir siteye girmeyi deneyin).
    *   KYK portalı (`wifi.gsb.gov.tr`) genel olarak erişilemez durumda olabilir.
*   **`.exe` Dosyası Çalışmıyor:**
    *   Antivirüs yazılımınızın dosyayı engellemediğinden emin olun.
    *   Gerekli tüm bağımlılıkların `.exe` dosyasına doğru şekilde paketlendiğinden emin olun (PyInstaller komutunu kontrol edin).
*   **Diğer Hatalar:** Herhangi bir beklenmedik davranış veya hata mesajı için öncelikle `kyk_login.log` dosyasını detaylı olarak inceleyin. Hata mesajları genellikle sorunun ne olduğu hakkında ipucu verir.

---
<!-- English version below -->
<!-- Aşağıda İngilizce versiyonu bulunmaktadır -->
---

# KYK Wi-Fi Auto Login & Quota Check Script v1.0.0

## **⚠️ Disclaimer ⚠️**

**This script is provided to demonstrate web automation techniques for educational purposes only.** It exemplifies how to interact with a web portal programmatically using Python.

**Do NOT use this script to exploit, interfere with, or disrupt the GSB/KYK Wi-Fi network or services.** Unauthorized access or interference with computer systems is illegal and unethical. The developers assume no liability and are not responsible for any misuse or damage caused by this script. Use at your own risk and responsibility. Ensure your use complies with the GSB/KYK terms of service.

---

*This project is not affiliated with, endorsed by, or sponsored by the Ministry of Youth and Sports (GSB) or the Credit and Dormitories Institution (KYK).*

---

## Overview

This project is a Python script (`v1.0.0`, filename: `kyk_wifi_helper.py`) that provides an automated way to log in to the GSB/KYK (Ministry of Youth and Sports / Credit and Dormitories Institution) dormitory Wi-Fi network (`wifi.gsb.gov.tr`), check the remaining internet quota, and manage the session.

It aims to offer a more stable and automated interaction with the KYK Wi-Fi portal, which can sometimes be unreliable or difficult to use. The script's purpose is solely to facilitate login and session management; it is not intended to bypass restrictions or misuse the network.

## Features

*   **Auto Login:** Automatically connects to the KYK Wi-Fi portal using your T.C. ID Number (Username) and password.
*   **Quota Check:** Displays your current remaining internet quota in Megabytes (MB).
*   **Keep-Alive:**
    *   **Normal Mode:** Prevents automatic session timeout by performing quota checks at regular intervals (default 10 minutes). Also displays the current quota information.
    *   **Fast Mode:** Keeps the session active with more frequent checks (default 10 seconds) without displaying quota info (for performance).
*   **Secure Credential Storage:** Optionally stores your login credentials (T.C. ID and password) securely in a local `.env` file created in the program's directory. This avoids the need to re-enter them on subsequent runs.
*   **Interactive Menu:** After a successful login, presents a user-friendly menu with various options: Show Remaining Quota, Keep-Alive (Normal/Fast), Change Credentials, Logout and Exit, Exit (Keep Session Alive).
*   **Default Option:** Pressing `Enter` in the menu without making a selection defaults to the "Show Remaining Quota" (Option 1) action.
*   **Change Credentials:** Allows you to enter a new T.C. ID Number and password via the menu while the program is running, saving these new credentials to the local `.env` file.
*   **Session Tracking:** Stores the active Wi-Fi session ID (`JSESSIONID`) in a temporary local file (`session_info.txt`) to facilitate logout and session management.
*   **Detailed Logging:** Records all significant operations (login attempts, success/failure status, quota checks, logouts, errors, etc.) with timestamps to a local file named `kyk_login.log`. Very useful for troubleshooting issues.
*   **First Run Helper:** On the first execution, the script offers to open this `README.md` file for guidance and asks if you want to save your credentials for future use.
*   **Graceful Shutdown:** Attempts to terminate the program cleanly when `Ctrl+C` is pressed. If possible, it logs out the active Wi-Fi session before exiting. `Ctrl+C` is also used to return to the main menu from the Keep-Alive modes.
*   **Colored Console Output:** Utilizes the `colorama` library (if installed) to provide colored console output for better readability.

## Repository Structure

*   `kyk_wifi_helper.py`: The main script file.
*   `requirements.txt`: File listing the required Python libraries.
*   `README.md`: This documentation file (Turkish/English).
*   `app_icon.ico`: Application icon (for .exe compilation).
*   `.env` (If created): Local file where username and password are stored.
*   `session_info.txt` (If created): Temporary local file storing active session information.
*   `kyk_login.log` (If created): Local log file containing operation records.
*   `.ilk_calistirma_tamam` (If created): Local marker file (may be hidden) to prevent showing the first-run helper again.
*   `build/`: Folder containing intermediate files generated during PyInstaller compilation.
*   `dist/`: Folder where the final distributable `.exe` file is placed after compilation.

## Requirements

*   **Python:** Python 3.x version must be installed.
*   **Libraries:** The following Python libraries need to be installed:
    *   `requests` (for making HTTP requests)
    *   `python-dotenv` (for managing the `.env` file)
    *   `beautifulsoup4` (for parsing HTML/XML)
    *   `lxml` (recommended, a faster parser for `beautifulsoup4`)
    *   `colorama` (optional, for colored console output)

## Installation (For Python Script)

1.  **Get the Project:** Download the project files or clone the repository using `git clone`.
2.  **Install Libraries:** Open a terminal or command prompt in the project directory and install the required libraries using `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
    Alternatively, install them individually:
    ```bash
    pip install requests python-dotenv beautifulsoup4 lxml colorama
    ```

## Downloading the Executable (.exe)

If you prefer not to install Python or build the script from source, you can use a pre-compiled version for Windows.

*   Go to the **[Releases](https://github.com/ozankoku/GSB-Wifi-Script/releases)** page of this repository.
*   Find the release tagged `v1.0.0` (or the latest version) and download the `.exe` file listed under "Assets".
*   You can run the downloaded `.exe` file directly without any installation.

## Building the Executable (.exe)

You can create your own `.exe` file using PyInstaller to run the script on Windows systems without Python installed or for easier sharing.

1.  **Install PyInstaller:** If you don't have it installed:
    ```bash
    pip install pyinstaller
    ```
2.  **Build `.exe`:** Open a terminal in the project's root directory and run the following command:
    ```bash
    pyinstaller --onefile --windowed --icon=app_icon.ico kyk_wifi_helper.py
    ```
    *   `--onefile`: Bundles all dependencies into a single executable file.
    *   `--windowed`: Prevents the command prompt window from appearing in the background (optional).
    *   `--icon=app_icon.ico`: Sets a custom icon for the application.

3.  **Result:** After a successful compilation, the generated `.exe` file will be located in the `dist` folder within your project directory.

## Usage

**Important:** For the script to log in successfully, your device must be connected to the KYK Wi-Fi network, **and** you should not have already logged in manually via the web portal.

1.  **Running the Script:**
    *   **Using `.exe`:** Double-click the `.exe` file that you downloaded or built.
    *   **As Python Script:** Open a terminal in the project directory and enter:
        ```bash
        python kyk_wifi_helper.py
        ```

2.  **First Run Experience:**
    *   If the `.env` file is not found, the script will prompt you to enter your T.C. ID Number (Username) and your KYK Wi-Fi password.
    *   It will then ask if you want to save these credentials to the local `.env` file for future use. Confirming with 'y' or 'e' will save them.
    *   You might also be asked if you want to open this `README.md` file for instructions.

3.  **Menu Navigation:**
    *   After a successful login, the main menu will be displayed.
    *   Enter the number corresponding to the desired action (1, 2, 3, 4, 5, 6) and press `Enter`.
    *   Pressing `Enter` without typing a number will execute the default option '1' (Show Remaining Quota).
    *   While in the "Keep-Alive" modes (Normal or Fast), press `Ctrl+C` to stop that mode and return to the main menu.
    *   To exit the program completely, either choose the relevant exit option from the menu (5 or 6) or press `Ctrl+C` (a second `Ctrl+C` usually terminates the program, attempting to log out first).

## Configuration

*   **`.env` File:** Upon your confirmation during the first run, the script saves the username and password locally in this file. The format is:
    ```dotenv
    KYK_USERNAME=YOUR_TC_ID_NUMBER
    KYK_PASSWORD=YOUR_PASSWORD
    ```
    You can also create or edit this file manually. Do not share the contents of this file for security reasons.
    *   If you delete the `.env` file, the script will prompt for credentials again on the next run.

## Logging

*   The script logs all significant activities and potential errors to a local file named `kyk_login.log`. If you encounter any problems, checking this file first is the best way to understand what went wrong.

## Important Notes

*   **Security:** The `.env` file contains your sensitive login credentials and is stored **only locally** on your computer. Keep the folder containing this file secure and avoid sharing its contents.
*   **Portal Changes:** If the structure of the KYK Wi-Fi portal website (HTML elements, form fields, URLs, etc.) changes, some functions of the script (especially login and quota checking) might break. The script would then need to be updated. Errors in the `kyk_login.log` file can provide clues about such issues.
*   **Network Connection:** The script requires an active connection to the KYK Wi-Fi network to function. Ensure you are connected before running it.
*   **Colorama:** The `colorama` library is used for colored console output. If it's not installed on your system, the script will still work, but the output will be monochrome.
*   **Responsible Use:** Please use this script responsibly, respecting the GSB/KYK network usage policies and terms of service. Avoid actions that could place an excessive load on the network infrastructure.

## Troubleshooting

*   **Login Failed:**
    *   First, double-check that your T.C. ID Number and password are correct.
    *   If using the `.env` file, verify its contents (should be in `KYK_USERNAME=...`, `KYK_PASSWORD=...` format). If unsure, try deleting the `.env` file and letting the script prompt you again.
    *   Open the `kyk_login.log` file and look for error messages like "CREDENTIAL_ERROR", "Hatali kullanici adi veya sifre", or similar indicators.
*   **Cannot Display Quota / Keep-Alive Not Working:**
    *   Check the `kyk_login.log` file for errors related to "ViewState", "AJAX", "SESSION_EXPIRED", or HTML parsing.
    *   This might indicate a temporary issue with the KYK portal or a change in its web structure (see Important Notes), potentially requiring a script update.
    *   If you see "SESSION_EXPIRED" errors, the script usually tries to log in again automatically. If it repeats constantly, there might be another underlying issue.
*   **Network Errors (`ConnectionError`, `Timeout`, etc.):**
    *   Ensure your device is properly connected to the KYK Wi-Fi network and has internet access (try visiting another website).
    *   The KYK portal itself (`wifi.gsb.gov.tr`) might be temporarily down or inaccessible.
*   **`.exe` File Not Working:**
    *   Check if your antivirus software is blocking the file. You might need to add an exception.
    *   Ensure all necessary dependencies were correctly bundled into the `.exe` during the PyInstaller process (review the build command).
*   **Other Errors:** For any unexpected behavior or error messages, the first step should always be to examine the `kyk_login.log` file in detail. The logged messages often pinpoint the source of the problem.