# ================================================
# =        KYK Wi-Fi Auto Login/Logout           =
# ================================================
#
from __future__ import annotations

import itertools
import logging
import os
import signal  # Ctrl+C sinyalini yakalamak icin
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv  # Guvenli giris bilgileri (.env dosyasi) icin
import xml.etree.ElementTree as ET  # XML analiz etmek icin alternatif

# --- Base Path Detection --- #
# Determine the base path depending on whether the script is running as a bundled executable or a standard Python script.


@dataclass(frozen=True)
class RuntimePaths:
    """Holds runtime paths regardless of execution environment."""

    base_path: Path
    project_root: Path


def detect_paths() -> RuntimePaths:
    """Determine runtime directories for both script and bundled executions."""

    if getattr(sys, "frozen", False):
        executable_path = Path(sys.executable).resolve()
        executable_dir = executable_path.parent
        project_root = executable_dir.parent
        base_path = executable_dir
    else:
        project_root = Path(__file__).resolve().parent
        base_path = project_root
    return RuntimePaths(base_path=base_path, project_root=project_root)


PATHS = detect_paths()

# --- Absolute Paths --- #
# Define absolute paths for runtime files relative to the base path (exe/script location)
DOTENV_PATH = PATHS.base_path / ".env"
SESSION_FILE_PATH = PATHS.base_path / "session_info.txt"
FIRST_RUN_MARKER_PATH = PATHS.base_path / ".ilk_calistirma_tamam"
LOG_FILE_PATH = PATHS.base_path / "kyk_login.log"
# Define README path relative to the determined project root
README_PATH = PATHS.project_root / "README.md"

# Renkli konsol ciktilari icin (istege bagli)
try:
    import colorama
    colorama.init(autoreset=True) # Renkleri her seferinde sifirla
    # Renk kodlari (Daha okunakli ciktilar icin)
    R = colorama.Fore.RED
    Y = colorama.Fore.YELLOW
    G = colorama.Fore.GREEN
    C = colorama.Fore.CYAN
    M = colorama.Fore.MAGENTA
    B = colorama.Fore.BLUE
    W = colorama.Fore.WHITE # Varsayilan Beyaz
    RS = colorama.Style.RESET_ALL # Renkleri sifirla
    BR = colorama.Style.BRIGHT # Parlak stil
except ImportError:
    # colorama kutuphanesi yoksa renk kullanilmaz
    print("Uyari: 'colorama' kutuphanesi yuklu degil. Renkli ciktilar gosterilemeyecek.")
    print("Lutfen 'pip install colorama' komutu ile yukleyin.")
    class DummyColor(str):
        def __new__(cls) -> "DummyColor":  # type: ignore[misc]
            return super().__new__(cls, "")

        def __getattr__(self, name: str) -> str:
            return ""

    R = Y = G = C = M = B = W = RS = BR = DummyColor()
    colorama = None

# --- DEBUG MODU --- #
# Gelistirici icin daha detayli hata ayiklama mesajlarini acar.
# Normal kullanicilar icin False kalmalidir.
DEBUG_MODE = False

# --- Global Exit Flag ---
# Ctrl+C yakalandiginda bu True olur.
exit_requested = False

# --- Signal Handler ---
def signal_handler(sig, frame):
    """Handles SIGINT (Ctrl+C) signals."""
    global exit_requested
    if not exit_requested: # Prevent multiple messages if signal is sent repeatedly
        # Use basic print here as logger might be busy or shutdown initiated
        print(f"\n{Y}{BR}Ctrl+C detected!{RS}{Y} Attempting graceful shutdown...{RS}")
        logging.info("SIGINT received, setting exit_requested flag.")
        exit_requested = True

# --- Bekleme Animasyonu --- #
# Konsolda bekleme sirasinda gorsel bir isaret gosterir.
def animated_sleep(duration: float, message: str = "Bekleniyor...", color: str | object = W) -> bool:
    """Eger konsol penceresi varsa, bekleme sirasinda bir animasyon gosterir."""

    global exit_requested  # Access the global flag
    if exit_requested:
        return True  # Exit immediately if already requested

    msvcrt_loaded = False
    if sys.platform == "win32":
        try:
            import msvcrt  # type: ignore

            msvcrt_loaded = True
        except ImportError:
            logging.debug("msvcrt module could not be imported on Windows.")

    if sys.stdout:
        spinner = itertools.cycle(["-", "\\", "|", "/"])
        end_time = time.monotonic() + duration
        turkish_chars = {
            "ı": "i",
            "İ": "I",
            "ğ": "g",
            "Ğ": "G",
            "ü": "u",
            "Ü": "U",
            "ş": "s",
            "Ş": "S",
            "ö": "o",
            "Ö": "O",
            "ç": "c",
            "Ç": "C",
        }
        ascii_message = message
        for tr, en in turkish_chars.items():
            ascii_message = ascii_message.replace(tr, en)

        formatted_message = f"{color}{ascii_message}{RS}" if colorama else ascii_message
        sys.stdout.write(formatted_message + " ")

        interrupted = False
        while time.monotonic() < end_time:
            if exit_requested:  # Check flag set by signal handler
                logging.debug("Exit requested flag detected during animated_sleep.")
                interrupted = True
                break

            # Check for keyboard input using msvcrt on Windows (for .exe)
            if msvcrt_loaded and msvcrt.kbhit():  # type: ignore[name-defined]
                try:
                    key = msvcrt.getch()  # type: ignore[name-defined]
                    if key == b"\x03":  # Ctrl+C pressed
                        logging.debug("Ctrl+C detected via msvcrt in animated_sleep.")
                        exit_requested = True  # Set the global flag
                        interrupted = True
                        break
                except Exception as e_msvcrt_get:  # pragma: no cover - platform specific
                    # Log error reading key, but continue
                    logging.debug("Error reading key with msvcrt: %s", e_msvcrt_get)

            # Animation update
            sys.stdout.write(next(spinner))
            sys.stdout.flush()

            # Shorter sleep to be more responsive to Ctrl+C
            check_interval = 0.1  # Check for input every 0.1s
            remaining_time_in_loop = end_time - time.monotonic()
            sleep_this_iteration = min(check_interval, max(0.0, remaining_time_in_loop))
            if sleep_this_iteration > 0:
                time.sleep(sleep_this_iteration)

            if not interrupted:  # Avoid erasing the spinner char if interrupted
                sys.stdout.write("\b")

        # Cleanup line after loop finishes or is interrupted
        clear_len = len(ascii_message) + 10  # Adjusted length
        sys.stdout.write("\r" + " " * clear_len + "\r")
        sys.stdout.flush()
        # No extra message here, handler prints one
        return interrupted  # Return True if exit was requested during sleep

    # Non-console sleep, check flag periodically
    end_time = time.monotonic() + duration
    while time.monotonic() < end_time:
        if exit_requested:
            return True
        sleep_chunk = min(0.2, max(0.0, end_time - time.monotonic()))
        if sleep_chunk > 0:
            time.sleep(sleep_chunk)  # Sleep in chunks
    return exit_requested  # Check one last time

# --- Kullanici Bilgilerini Alma --- #
# Program icin gerekli olan KYK kullanici adi ve sifresini alir.
# Eger daha once kaydedilmisse, .env dosyasindan okur, degilse kullaniciya sorar.
def get_credentials() -> Tuple[Optional[str], Optional[str], str]:
    """Kullanici adi ve sifreyi .env dosyasindan veya kullanicidan alir."""

    username = os.getenv("KYK_USERNAME")
    password = os.getenv("KYK_PASSWORD")
    source = "env"

    if not username or not password:
        source = "user"
        print(f"{Y}Giris bilgileri .env dosyasinda bulunamadi veya .env dosyasi eksik.{RS}")
        # Reset both if either is missing
        username = None
        password = None
        print(f"{M}{'-'*60}{RS}")
        print(f"{C}Not: T.C. Kimlik Numaraniz ve KYK sifreniz, sadece KYK/GSB Wi-Fi portalina giris yapmak icin kullanilir. Bu bilgiler program tarafindan baska hicbir yere gonderilmez, kaydedilmez (siz '.env' dosyasina kaydetmeyi onaylamadikca) veya goruntulenemez. Gelistirici dahil kimsenin bilgilerinize erisimi yoktur.{RS}") # Added more detailed note
        print(f"{M}{'-'*60}{RS}")
        while not username:
            username = input(f"{W}Lutfen KYK Kullanici Adinizi (TC Kimlik No) girin: {RS}").strip()
            if not username:
                print(f"{R}Kullanici adi bos olamaz.{RS}")
        while not password:
            password = input(f"{W}Lutfen KYK Sifrenizi girin: {RS}").strip()
            if not password:
                print(f"{R}Sifre bos olamaz.{RS}")
        # Saving prompt is moved to the main block after validation
    else:
        logging.info(f"Giris bilgileri .env dosyasindan basariyla yuklendi.")

    return username, password, source

# --- Oturum Bilgi Dosyasi --- #
# Aktif internet oturumunun kimligi (JSESSIONID) gecici olarak bu dosyada saklanir.
SESSION_FILE = SESSION_FILE_PATH

# --- KYK Portal Adresleri ve Zaman Ayarlari --- #
# GSB Wi-Fi sistemine baglanmak icin kullanilan adresler ve zamanlama ayarlari.
LOGIN_URL = "https://wifi.gsb.gov.tr/login.html" # Giris sayfasi
CHECK_URL = "https://wifi.gsb.gov.tr/j_spring_security_check" # Giris dogrulama adresi
SUCCESS_URL = "https://wifi.gsb.gov.tr/" # Basarili giris sonrasi adres (ve AJAX hedefi)
AJAX_INTERVAL = 600 # Oturumu acik tutma modunda kota kontrol araligi (saniye) - 10 dakika
FAST_AJAX_INTERVAL = 10 # Hizli oturumu acik tutma modunda kota kontrol araligi (saniye) - 30 saniye
RETRY_DELAY = 60 # Basarisiz giristen sonra yeniden deneme gecikmesi (saniye) - 1 dakika
REQUEST_TIMEOUT = 30 # Internet istekleri icin zaman asimi suresi (saniye)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0"
)
SEC_CH_UA = '"Microsoft Edge";v="135", "Not-A.Brand";v="8", "Chromium";v="135"'


def compose_headers(**overrides: str) -> Dict[str, str]:
    """Merge provided overrides with a shared base header configuration."""

    base_headers: Dict[str, str] = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "tr,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
        "Connection": "keep-alive",
        "DNT": "1",
        "sec-ch-ua": SEC_CH_UA,
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    base_headers.update(overrides)
    return base_headers


QuotaResult = Tuple[Optional[Dict[str, str]] | str, Optional[str]]

# --- Kayit (Loglama) Ayarlari --- #
# Programin calisma adimlarinin ve hatalarin kaydedilmesi icin ayarlar.
# Kayitlar hem konsola hem de 'kyk_login.log' dosyasina yazilir.

MAX_LOGIN_ATTEMPTS = 3 # Izin verilen maksimum GENEL deneme sayisi (Network vb. hatalar icin)
MAX_CREDENTIAL_ATTEMPTS = 3 # Izin verilen maksimum HATALI GIRIS denemesi sayisi

# Renkli konsol cikti formatlayicisi
class ColorFormatter(logging.Formatter):
    """Konsol icin renkli log formatlayicisi."""
    FORMATS = {
        logging.DEBUG:    f"%(asctime)s - {C}{BR}%(levelname)s{RS}{C} - %(message)s{RS}",
        logging.INFO:     f"{G}%(message)s{RS}",
        logging.WARNING:  f"%(asctime)s - {Y}{BR}%(levelname)s{RS}{Y} - %(message)s{RS}",
        logging.ERROR:    f"%(asctime)s - {R}{BR}%(levelname)s{RS}{R} - %(message)s{RS}",
        logging.CRITICAL: f"%(asctime)s - {R}{BR}%(levelname)s{RS}{R} - %(message)s{RS}",
    }
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
logger = logging.getLogger()
logger.setLevel(log_level)
if logger.hasHandlers(): logger.handlers.clear()

# Dosya Kayit Ayari (Renksiz)
try:
    LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
except Exception as e_fh:
    print(f"{R}Hata: Log dosyasi (kyk_login.log) olusturulamadi/yazilamadi: {e_fh}{RS}")

# Konsol Kayit Ayari (Renkli)
if sys.stdout:
    try:
        console_handler = logging.StreamHandler(sys.stdout)
        if colorama:
            console_handler.setFormatter(ColorFormatter())
        else:
            console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)
    except Exception as e_ch:
        print(f"{R}Hata: Konsol loglama ayarlanamadi: {e_ch}{RS}")

# --- Ana Islevler --- #
# Programin temel gorevlerini yerine getiren fonksiyonlar.

# KYK Wi-Fi Portalina Giris Islemi
def login_attempt(session: requests.Session) -> bool | str:
    """Verilen oturum (session) ile KYK Wi-Fi portalina giris yapmayi dener."""
    try:
        logging.info(f"Giris sayfasi aliniyor: {LOGIN_URL}")
        headers_get = compose_headers(
            Accept="text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            **{
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        response_get = session.get(LOGIN_URL, headers=headers_get, timeout=REQUEST_TIMEOUT, verify=True)
        response_get.raise_for_status()
        logging.info("Giris sayfasi basariyla alindi. Ilk cerezler (cookies) alindi.")

        login_data = {
            'j_username': USERNAME,
            'j_password': PASSWORD,
            'submit': 'Giris'
        }
        headers_post = compose_headers(
            Accept="text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            **{
                'Cache-Control': 'max-age=0',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://wifi.gsb.gov.tr',
                'Referer': LOGIN_URL,
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
            }
        )

        logging.info(f"Giris bilgileri gonderiliyor: {CHECK_URL}")
        response_post = session.post(
            CHECK_URL,
            headers=headers_post,
            data=login_data,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=False,
            verify=True
        )

        logging.info(f"Giris POST yanit durumu (status code): {response_post.status_code}")
        BASE_SUCCESS_URL = SUCCESS_URL

        redirect_location = response_post.headers.get('Location')
        # Check for exact match to avoid considering error pages as success
        if response_post.status_code == 302 and redirect_location and redirect_location == BASE_SUCCESS_URL:
            logging.info(f"Giris basarili! Oturum acildi (Yonlendirme: {redirect_location}).")
            jsessionid = session.cookies.get('JSESSIONID')
            if jsessionid:
                try:
                    with open(SESSION_FILE_PATH, "w") as f:
                        f.write(jsessionid)
                    logging.info(f"Oturum kimligi {SESSION_FILE_PATH} dosyasina kaydedildi.")
                except Exception as e:
                    logging.error(f"{SESSION_FILE_PATH} dosyasina oturum kimligi kaydedilemedi: {e}")
            else:
                logging.warning("Basarili giristen sonra oturumda JSESSIONID cerezi bulunamadi.")
            return True
        else:
            logging.warning(f"Giris basarisiz. Durum: {response_post.status_code}, Beklenen Yonlendirme (benzeri): {BASE_SUCCESS_URL}, Gelen Yonlendirme: {redirect_location}")
            is_credential_error = False
            error_message_found = False
            # Check for redirect back to login page first
            if redirect_location and LOGIN_URL in redirect_location:
                logging.debug("Giris sayfasina geri yonlendirildi, muhtemelen hatali giris bilgisi.")
                is_credential_error = True # Assume credential error on redirect to login
                try:
                    # Fetch the content of the redirected page to confirm
                    error_page_resp = session.get(redirect_location, headers=headers_get, timeout=REQUEST_TIMEOUT, verify=True)
                    body_text = error_page_resp.text
                    if "hatali kullanici adi veya sifre" in body_text.lower() or \
                       "gecersiz kullanici adi veya parola" in body_text.lower() or \
                       "kimlik bilgileri dogrulanamadi" in body_text.lower():
                        logging.warning("Geri yonlendirilen sayfada hatali giris bilgisi mesaji tespit edildi.")
                        error_message_found = True
                    else:
                        logging.debug(f"Geri yonlendirilen sayfa ozeti (Hata mesaji olabilir): {body_text[:500]}...")
                except Exception as e_redir:
                     logging.warning(f"Geri yonlendirme sayfasindan ({redirect_location}) hata mesaji alinirken hata olustu: {e_redir}")

            # If no redirect, check the response body
            elif response_post.status_code != 302: # Check body only if not a redirect
                try:
                    body_text = response_post.text
                    if "hatali kullanici adi veya sifre" in body_text.lower() or \
                       "gecersiz kullanici adi veya parola" in body_text.lower() or \
                       "kimlik bilgileri dogrulanamadi" in body_text.lower():
                        logging.warning("Yanit iceriginde hatali giris bilgisi mesaji tespit edildi.")
                        is_credential_error = True
                        error_message_found = True
                    # Log body summary only if no specific error found, to avoid redundancy
                    if not error_message_found:
                        logging.warning(f"Yanit Govdesi Ozeti (Hata mesaji olabilir): {body_text[:500]}...")
                except Exception as e_body:
                    logging.warning(f"POST yanit govdesi okunamadi: {e_body}")

            if is_credential_error:
                logging.warning("Kullanici adi veya sifre hatali gorunuyor.")
                return "CREDENTIAL_ERROR" # Specific return for credential issues
            else:
                # General failure if not a credential error
                logging.error("Giris basarisiz oldu (Detaylar yukarida).")
            return False

    except requests.exceptions.Timeout:
        logging.error(f"Ag istegi {REQUEST_TIMEOUT} saniye sonra zaman asimina ugradi. Internet baglantinizi kontrol edin.")
        return False
    except requests.exceptions.ConnectionError as e:
        logging.error(f"Ag baglanti hatasi: {e}. KYK Wi-Fi agina bagli oldugunuzdan ve portalin erisilebilir oldugundan emin olun.")
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"HTTP istegi sirasinda bir hata olustu: {e}")
        return False
    except Exception as e:
        logging.error(f"Giris denemesi sirasinda beklenmeyen bir hata olustu: {e}", exc_info=True)
        return False

# Oturumun Aktif Kalmasi Icin Gerekli Bilgiyi (ViewState) Alma
def get_initial_viewstate(session: requests.Session) -> Optional[str]:
    """Basarili giristen sonra ana sayfadan ilk ViewState degerini alir."""
    try:
        logging.info(f"Basarili giris sayfasi ({SUCCESS_URL}) aliniyor (ViewState icin)...")
        headers = compose_headers(
            Accept="text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            Referer=LOGIN_URL,
            **{
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        response = session.get(SUCCESS_URL, headers=headers, timeout=REQUEST_TIMEOUT, verify=True)
        response.raise_for_status()

        if LOGIN_URL in response.url:
             logging.error("ViewState alinirken giris sayfasina yonlendirildi! Oturum kaybolmus olabilir.")
             return None

        soup = BeautifulSoup(response.text, 'html.parser')
        viewstate_input = soup.find('input', {'name': 'javax.faces.ViewState'})

        if viewstate_input and 'value' in viewstate_input.attrs:
            vs_value = viewstate_input['value']
            logging.info(f"Ilk ViewState degeri bulundu.")
            logging.debug(f"Tam ViewState: ...{vs_value[-20:]}") # Sadece sonunu logla
            return vs_value
        else:
            logging.error("Sayfa HTML'inde javax.faces.ViewState input'u bulunamadi.")
            logging.debug(f"ViewState aranan HTML (ilk 500 char):\n{response.text[:500]}")
            return None

    except requests.exceptions.RequestException as e:
        logging.error(f"ViewState almak icin sayfa getirilirken hata: {e}")
        return None
    except Exception as e:
        logging.error(f"ViewState parse edilirken hata: {e}", exc_info=True)
        return None

# Kota Bilgisini Internetten Sorgulama
def get_quota_ajax(session: requests.Session, current_view_state: Optional[str]) -> QuotaResult:
    """Verilen ViewState ile AJAX kullanarak kota bilgisini sorgular."""
    if not current_view_state:
        logging.error("AJAX istegi icin ViewState mevcut degil.")
        return None, None

    logging.debug("Kota bilgisi icin AJAX istegi gonderiliyor...")
    ajax_headers = compose_headers(
        Accept="application/xml, text/xml, */*; q=0.01",
        **{
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Faces-Request': 'partial/ajax',
            'Origin': 'https://wifi.gsb.gov.tr',
            'Referer': SUCCESS_URL,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest',
        }
    )
    ajax_data = {
        'javax.faces.partial.ajax': 'true',
        'javax.faces.source': 'mainPanel:kota:j_idt122',
        'javax.faces.partial.execute': '@all',
        'javax.faces.partial.render': 'mainPanel:kota',
        'mainPanel:kota:j_idt122': 'mainPanel:kota:j_idt122',
        'mainPanel:kota': 'mainPanel:kota',
        'javax.faces.ViewState': current_view_state
    }

    try:
        response = session.post(SUCCESS_URL, headers=ajax_headers, data=ajax_data, timeout=REQUEST_TIMEOUT, verify=True)

        if response.headers.get('Content-Type', '').startswith('text/html'):
            logging.error("AJAX istegine XML yerine HTML yaniti alindi. Oturum zaman asimina ugramis olabilir.")
            return "SESSION_EXPIRED", None

        response.raise_for_status()
        logging.debug(f"AJAX yanit durumu: {response.status_code}")

        parser = 'lxml-xml' if 'lxml' in sys.modules else 'xml'
        soup_xml = BeautifulSoup(response.content, parser)

        quota_update = soup_xml.find('update', {'id': 'mainPanel:kota'})
        new_viewstate_update = soup_xml.find('update', {'id': 'j_id1:javax.faces.ViewState:0'})

        quota_html_content = None
        if quota_update and quota_update.string:
            quota_html_content = quota_update.string
        else:
            logging.error("AJAX yanitinda 'mainPanel:kota' update'i bulunamadi veya bos.")
            new_vs = None
            if new_viewstate_update and new_viewstate_update.string:
                 new_vs = new_viewstate_update.string
                 logging.debug(f"Yeni ViewState alindi (kota update'i olmadan): ...{new_vs[-20:]}")
            else:
                 logging.warning("AJAX yanitinda ViewState update'i de bulunamadi.")
            return None, new_vs

        new_view_state = None
        if new_viewstate_update and new_viewstate_update.string:
            new_view_state = new_viewstate_update.string
            logging.debug(f"AJAX yanitindan yeni ViewState alindi: ...{new_view_state[-20:]}")
        else:
            logging.error("AJAX yanitinda ViewState update'i bulunamadi! Sonraki istekler basarisiz olabilir.")
            new_view_state = current_view_state

        quota_value = None
        if quota_html_content:
            soup_html = BeautifulSoup(quota_html_content, 'html.parser')
            try:
                target_label_text = "Toplam Kalan Kota (MB):"
                label_element = soup_html.find('label', string=lambda t: t and target_label_text in t.strip())
                if label_element:
                    parent_td = label_element.find_parent('td')
                    if parent_td:
                        value_td = parent_td.find_next_sibling('td')
                        if value_td:
                            value_label = value_td.find('label')
                            if value_label:
                                quota_mb = value_label.get_text(strip=True)
                                quota_value = f"{quota_mb} MB"
                                logging.debug(f"AJAX'tan cikarilan kota degeri: {quota_value}")
                            else: logging.warning("AJAX HTML'inde deger label'i bulunamadi.")
                        else: logging.warning("AJAX HTML'inde deger TD'si bulunamadi.")
                    else: logging.warning("AJAX HTML'inde parent TD bulunamadi.")
                else:
                    logging.warning(f"AJAX HTML'i icinde '{target_label_text}' etiketi bulunamadi.")
                    logging.debug(f"AJAX HTML Content for Quota:\n{quota_html_content}")
            except Exception as e_html_parse:
                logging.warning(f"Kota HTML'i parse edilirken hata: {e_html_parse}")
                logging.debug(f"Kota parse hatasi alan HTML: {quota_html_content}", exc_info=True)

        quota_dict = None
        if quota_value:
            quota_dict = {"Toplam Kalan Kota": quota_value}

        return quota_dict, new_view_state

    except requests.exceptions.Timeout:
        logging.error(f"AJAX istegi {REQUEST_TIMEOUT} saniye sonra zaman asimina ugradi.")
        return None, current_view_state
    except requests.exceptions.RequestException as e:
        logging.error(f"AJAX istegi sirasinda hata: {e}")
        return None, current_view_state
    except Exception as e:
        logging.error(f"AJAX yaniti islenirken hata: {e}", exc_info=True)
        return None, current_view_state

# KYK Wi-Fi Oturumunu Kapatma Islemi
def perform_logout(jsessionid_value: str) -> bool:
    """Verilen oturum kimligi (JSESSIONID) ile KYK Wi-Fi portalindan cikis yapmayi dener."""
    LOGOUT_URL = "https://wifi.gsb.gov.tr/login.html?logout=1"
    REQUEST_TIMEOUT = 20
    SUCCESS_MESSAGE_FRAGMENT = "Basari ile cikis yaptiniz"

    if not jsessionid_value:
        logging.error("(Logout) Oturum kimligi (JSESSIONID) degeri bos olamaz.")
        return False

    logging.info(f"(Logout) JSESSIONID ile oturum kapatilmaya calisiliyor: ...{jsessionid_value[-6:]}")
    try:
        headers = compose_headers(
            Accept="text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            **{'Cookie': f'JSESSIONID={jsessionid_value}'}
        )
        response = requests.get(LOGOUT_URL, headers=headers, timeout=REQUEST_TIMEOUT, verify=True)
        response.raise_for_status()

        if SUCCESS_MESSAGE_FRAGMENT in response.text:
             logging.info("(Logout) Cikis basarili! Sunucu onay mesaji dondu.")
             try:
                 if SESSION_FILE_PATH.exists():
                     SESSION_FILE_PATH.unlink()
                     logging.info(f"(Logout) Oturum dosyasi silindi: {SESSION_FILE_PATH}")
             except Exception as e:
                 logging.warning(f"(Logout) Oturum dosyasi {SESSION_FILE_PATH} silinemedi: {e}")
             return True
        else:
             logging.warning("(Logout) Cikis istegi gonderildi (Yanit Kodu 200 OK), ancak onay mesaji yanitta bulunamadi.")
             logging.warning("(Logout) Oturum buyuk ihtimalle sunucu tarafindan sonlandirildi, ancak dogrulanamadi.")
             try:
                 if SESSION_FILE_PATH.exists():
                     SESSION_FILE_PATH.unlink()
                     logging.info(f"(Logout) Oturum dosyasi (dogrulanamasa da) silindi: {SESSION_FILE_PATH}")
             except Exception as e:
                 logging.warning(f"(Logout) Oturum dosyasi {SESSION_FILE_PATH} silinemedi: {e}")
             return True

    except requests.exceptions.Timeout:
        logging.error(f"(Logout) Cikis istegi {REQUEST_TIMEOUT} saniye sonra zaman asimina ugradi.")
        return False
    except requests.exceptions.ConnectionError as e:
        logging.error(f"(Logout) Baglanti hatasi nedeniyle cikis basarisiz: {e}.")
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"(Logout) Cikis istegi sirasinda bir hata olustu: {e}")
        return False
    except Exception as e:
        logging.error(f"(Logout) Cikis sirasinda beklenmeyen bir hata olustu: {e}", exc_info=True)
        return False

# --- Giris Bilgilerini Degistirme Islevi ---
def handle_credential_change(current_session: requests.Session) -> requests.Session:
    """Kullanicidan yeni giris bilgileri alir, .env dosyasini gunceller, global degiskenleri ayarlar ve mevcut oturumu sonlandirir."""
    global USERNAME, PASSWORD, logged_in, last_view_state, login_attempts, session # Declare globals we modify

    logging.info("Giris bilgileri degistiriliyor...")
    print(f"\n{Y}--- Giris Bilgilerini Guncelleme ---{RS}") # Add a header and newline
    print(f"{Y}Lutfen yeni giris bilgilerini girin.{RS}")
    new_username = ""
    new_password = ""
    while not new_username:
        new_username = input(f"{W}Yeni KYK Kullanici Adinizi (TC Kimlik No) girin: {RS}").strip()
        if not new_username:
            print(f"{R}Kullanici adi bos olamaz.{RS}")
    while not new_password:
        new_password = input(f"{W}Yeni KYK Sifrenizi girin: {RS}").strip()
        if not new_password:
            print(f"{R}Sifre bos olamaz.{RS}")

    try:
        with open(DOTENV_PATH, "w") as f:
            f.write(f"KYK_USERNAME={new_username}\\n")
            f.write(f"KYK_PASSWORD={new_password}\\n")
        logging.info(f"Giris bilgileri .env dosyasina kaydedildi.")

        # Update global variables
        USERNAME = new_username
        PASSWORD = new_password
        load_dotenv(override=True) # Reload to ensure consistency
        print(f"{G}Giris bilgileri basariyla guncellendi.{RS}")

        # Force logout of the current session if it exists and was logged in
        if logged_in and current_session:
            logging.info("Mevcut oturum kapatiliyor...")
            jsessionid_to_logout = current_session.cookies.get('JSESSIONID')
            if not jsessionid_to_logout:
                try:
                    if SESSION_FILE_PATH.exists():
                        jsessionid_to_logout = SESSION_FILE_PATH.read_text(encoding="utf-8").strip()
                except Exception as e_read_sess:
                    logging.warning(f"Oturum kapatma icin {SESSION_FILE_PATH} okunurken hata: {e_read_sess}")

            if jsessionid_to_logout:
                if perform_logout(jsessionid_to_logout):
                    logging.info("Guncelleme sonrasi mevcut oturum kapatildi.")
                else:
                    logging.warning("Guncelleme sonrasi mevcut oturum kapatilamadi veya dogrulanamadi.")
            else:
                logging.warning("Kapatilacak aktif oturum bulunamadi, ancak devam ediliyor.")

        # Reset state to force re-login attempt
        logged_in = False
        last_view_state = None
        login_attempts = 0 # Reset general login attempts too
        new_session = requests.Session() # Create a new session for the new credentials
        print(f"{Y}Yeni bilgilerle tekrar giris yapilacak...{RS}")
        animated_sleep(2, "Yeniden baslatiliyor...", color=Y) # Don't check interruption here, let loop handle it
        return new_session # Return the new session

    except Exception as e:
        logging.error(f".env dosyasina yeni bilgiler kaydedilirken/islenirken hata olustu: {e}")
        print(f"{R}Giris bilgileri guncellenemedi.{RS}")
        # Reload old credentials in case globals were partially changed
        USERNAME, PASSWORD, _ = get_credentials()
        print(f"{Y}------------------------------------{RS}\n") # Add separator
        animated_sleep(2, "Hata...", color=R) # Don't check interruption here
        return current_session # Return the old session on error

# --- Ana Program Akisi --- #
# Programin basladigi ve kullanici etkilesiminin yonetildigi ana bolum.
if __name__ == "__main__":
    # Register signal handler early
    signal.signal(signal.SIGINT, signal_handler)
    logging.debug("SIGINT handler registered.")

    # --- Program Imzasi ve Bilgileri --- #
    PROGRAM_NAME = "KYK Wi-Fi Giris Scripti"
    VERSION = "1.0.0"
    AUTHOR = "RianNoval"
    RELEASE_DATE = "2025-04-12"

    # Program basligini goster
    ascii_art = rf"""{BR}{B}
  ________  ___________________           __      __.______________.___
 /  _____/ /   _____/\______   \         /  \    /  \   \_   _____/|   |
/   \  ___ \_____  \  |    |  _/  ______ \   \/\/   /   ||    __)  |   |
\    \_\  \/        \ |    |   \ /_____/  \        /|   ||     \   |   |
 \______  /_______  / |______  /           \__/\/\/ |___|\___  /   |___|
        \/        \/         \/                 \/           \/
    {RS}"""
    print(ascii_art)
    print(f"{C}--- {PROGRAM_NAME} ---{RS}")
    print(f"{C}Versiyon:{RS} {Y}{VERSION}{RS}")
    print(f"{C}Gelistiren:{RS} {Y}{AUTHOR}{RS}")
    print(f"{C}Tarih:{RS} {Y}{RELEASE_DATE}{RS}")
    print(f"{M}{'='*40}{RS}\n")

    # --- Ilk Calistirma Kontrolu ve BENIOKU --- #
    # Program ilk kez calistiriliyorsa, kullanim kilavuzunu acmayi onerir.
    first_run_marker = FIRST_RUN_MARKER_PATH
    try:
        if not first_run_marker.exists():
            print(f"{Y}\n--------------------------------------------------------{RS}")
            readme_prompt = input(f" {Y}Programi ilk kez calistiriyorsunuz. \n {W}Kullanim kilavuzunu (README.md) acmak ister misiniz? (Y/N):{RS} ").strip().lower()
            print(f"{Y}--------------------------------------------------------\n{RS}")

            if readme_prompt in ['e', 'evet', 'y', 'yes']:
                try:
                    readme_path = README_PATH
                    if readme_path.exists():
                        absolute_readme_path = readme_path.resolve()
                        print(f"{C}'{absolute_readme_path}' acilmaya calisiliyor...{RS}")
                        if sys.platform == 'win32':
                            os.startfile(str(absolute_readme_path))
                        else:
                             try:
                                 import subprocess
                                 if sys.platform == 'darwin': subprocess.call(('open', str(absolute_readme_path)))
                                 else: subprocess.call(('xdg-open', str(absolute_readme_path)))
                             except (OSError, ImportError):
                                 print(f"{R}Hata: Bu isletim sisteminde dosya otomatik acilamiyor. Lutfen {readme_path} dosyasini manuel olarak acin.{RS}")
                    else:
                        print(f"{R}Hata: '{readme_path}' dosyasi bu klasorde bulunamadi.{RS}")
                except Exception as e:
                    print(f"{R}'{readme_path}' acilirken bir hata olustu: {e}{RS}")
                    logging.debug("BENIOKU acma hatasi:", exc_info=True)

            try:
                first_run_marker.write_text(time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")
                logging.debug(f"Ilk calistirma isaretcisi ({first_run_marker}) olusturuldu.")
                if sys.platform == 'win32':
                    try:
                        import ctypes
                        FILE_ATTRIBUTE_HIDDEN = 0x02
                        ctypes.windll.kernel32.SetFileAttributesW(str(first_run_marker), FILE_ATTRIBUTE_HIDDEN)
                        logging.debug(f"Ilk calistirma isaretcisi gizlendi (Windows).")
                    except Exception as hide_err:
                        logging.warning(f"Isaretci dosyasi ('{first_run_marker}') gizlenirken hata olustu: {hide_err}")
                        logging.debug("Isaretci gizleme hatasi:", exc_info=True)
            except Exception as e_marker:
                logging.warning(f"Ilk calistirma isaretcisi olusturulamadi: {e_marker}")
                logging.debug("Ilk calistirma isaretcisi olusturma hatasi:", exc_info=True)
    except Exception as e_first_run:
         logging.error(f"Ilk calistirma kontrolu sirasinda hata olustu.", exc_info=False)
         logging.debug("Ilk calistirma genel hatasi:", exc_info=True)

    # --- Ana Program Dongusu --- #
    logging.info("KYK Otomatik Giris & Kota Kontrol Scripti Baslatiliyor...")

    # --- Get Credentials & Initial Setup ---
    load_dotenv(dotenv_path=DOTENV_PATH)
    USERNAME, PASSWORD, cred_source = get_credentials()
    if not USERNAME or not PASSWORD:
        print(f"{R}Hata: Giris bilgileri alinamadi. Programdan cikiliyor.{RS}")
        sys.exit(1)

    session = requests.Session() # Internet istekleri icin oturum olustur
    logged_in = False # Giris durumu bayragi
    last_view_state = None # Kota sorgusu icin gerekli bilgi
    login_attempts = 0 # Basarisiz genel giris denemesi sayaci
    credential_error_attempts = 0 # Basarisiz HATALI GIRIS denemesi sayaci
    save_credentials_requested = False # Flag to save credentials after successful validation

    # --- Initial Validation (if credentials came from user) ---
    if cred_source == 'user':
        print() # Add separation
        save_prompt = input(f"{Y}Bu bilgileri dogruladiktan sonra ileride kullanmak uzere .env dosyasina kaydetmek ister misiniz? (Y/N): {RS}").strip().lower()
        if save_prompt in ['e', 'evet', 'y', 'yes']:
            save_credentials_requested = True
        else:
            print(f"{C}Giris bilgileri kaydedilmeyecek.{RS}")
        print() # Add separation

        logging.info("Kullanici tarafindan girilen bilgilerle ilk giris denemesi yapiliyor...")
        while credential_error_attempts < MAX_CREDENTIAL_ATTEMPTS and login_attempts < MAX_LOGIN_ATTEMPTS:
            if exit_requested: break # Allow exit during validation

            animated_interrupted = animated_sleep(2, "Giris deneniyor...", color=C)
            if animated_interrupted or exit_requested: break

            login_result = login_attempt(session)

            if login_result is True:
                logged_in = True
                credential_error_attempts = 0
                login_attempts = 0
                logging.info("="*30)
                logging.info(f"{G}   ILK GIRIS BASARILI{RS}")
                logging.info("="*30)
                print()
                animated_interrupted = animated_sleep(1, "Oturum bilgileri aliniyor (ViewState)...", color=C)
                if animated_interrupted or exit_requested: break
                last_view_state = get_initial_viewstate(session)
                if not last_view_state:
                    logging.warning("Basarili giristen sonra ilk ViewState alinamadi. Kota kontrolu calismayabilir.")

                # Save credentials ONLY if validation was successful AND user requested it initially
                if save_credentials_requested:
                    try:
                        with open(DOTENV_PATH, "w") as f:
                            f.write(f"KYK_USERNAME={USERNAME}\n")
                            f.write(f"KYK_PASSWORD={PASSWORD}\n")
                        print(f"{G}Giris bilgileri .env dosyasina kaydedildi.{RS}")
                        load_dotenv(override=True) # Ensure env is up-to-date
                    except Exception as e:
                        print(f"{R}.env dosyasina kaydederken hata olustu: {e}{RS}")
                        logging.error(f"Basarili dogrulama sonrasi .env kaydi basarisiz: {e}", exc_info=True)
                break # Exit validation loop

            elif login_result == "CREDENTIAL_ERROR":
                credential_error_attempts += 1
                logging.warning(f"Ilk dogrulama sirasinda hatali kullanici adi veya sifre tespit edildi (Deneme {credential_error_attempts}/{MAX_CREDENTIAL_ATTEMPTS}).")
                save_credentials_requested = False # Don't save initially wrong credentials

                if credential_error_attempts < MAX_CREDENTIAL_ATTEMPTS:
                    print(f"\n{R}--- HATALI GIRIS BILGISI ---{RS}")
                    print(f"{Y}Girdiginiz kullanici adi veya sifre yanlis.{RS}")
                    print(f"{Y}Kalan deneme hakkiniz: {MAX_CREDENTIAL_ATTEMPTS - credential_error_attempts}{RS}")
                    print(f"{W}Lutfen bilgileri tekrar girin:{RS}")
                    new_username = ""
                    new_password = ""
                    while not new_username:
                        new_username = input(f"{W}KYK Kullanici Adinizi (TC Kimlik No) girin: {RS}").strip()
                        if not new_username:
                            print(f"{R}Kullanici adi bos olamaz.{RS}")
                    while not new_password:
                        new_password = input(f"{W}KYK Sifrenizi girin: {RS}").strip()
                        if not new_password:
                            print(f"{R}Sifre bos olamaz.{RS}")
                    USERNAME = new_username # Update global USERNAME
                    PASSWORD = new_password # Update global PASSWORD
                    session = requests.Session() # Reset session for new attempt
                    print() # Add separation
                    continue # Retry validation with new credentials
                else:
                    logging.error(f"Ilk dogrulama sirasinda {MAX_CREDENTIAL_ATTEMPTS} kez hatali giris denemesi yapildi. Program durduruluyor.")
                    print(f"\n{R}Maksimum hatali giris deneme hakkina ulasildi.{RS}")
                    animated_interrupted = animated_sleep(5, "Kapatiliyor...", color=R)
                    exit_without_logout = True
                    break # Exit validation loop (will lead to sys.exit)

            else: # login_result is False (Network or other error)
                login_attempts += 1
                credential_error_attempts = 0 # Reset credential counter on other errors
                logging.warning(f"Ilk dogrulama sirasinda giris basarisiz (Network/Sunucu Hatasi?). {RETRY_DELAY} saniye sonra tekrar denenecek ({login_attempts}/{MAX_LOGIN_ATTEMPTS})...")
                print() # Add newline before retry sleep
                animated_interrupted = animated_sleep(RETRY_DELAY, f"{RETRY_DELAY} sn sonra tekrar denenecek...", color=Y)
                if animated_interrupted or exit_requested: break # Check after sleep
                session = requests.Session() # Reset session fully on general errors
                continue # Retry validation

        # After validation loop: Check if we exited due to failure
        if not logged_in:
            logging.error("Ilk giris dogrulamasi basarisiz oldu veya kullanici tarafindan iptal edildi. Programdan cikiliyor.")
            sys.exit(1) # Exit if validation failed

    # --- Main Program Loop --- #
    try:
        exit_without_logout = False # Programdan cikarken oturumu kapatma bayragi (re-init just in case)
        if exit_requested: # Check if exit was requested during setup/validation
            raise KeyboardInterrupt # Use an exception to jump to finally block

        while True: # Ana calisma dongusu
            if exit_requested: # Check flag at the start of the main loop
                 logging.info("Exit requested flag detected at main loop start.")
                 break

            # --- Login Attempt (if not already logged in during initial validation) --- #
            if not logged_in:
                if login_attempts < MAX_LOGIN_ATTEMPTS:
                    logging.info(f"Giris denemesi yapiliyor (Genel deneme {login_attempts + 1}/{MAX_LOGIN_ATTEMPTS})...")
                    animated_interrupted = animated_sleep(2, "Giris deneniyor...", color=C)
                    if animated_interrupted or exit_requested: break # Check after sleep

                    login_result = login_attempt(session)

                    if login_result is True:
                        logged_in = True
                        login_attempts = 0 # Reset general attempts on success
                        credential_error_attempts = 0 # Reset credential attempts on success
                        last_view_state = None
                        logging.info("="*30)
                        logging.info(f"{G}   KYK WIFI OTURUMU ACILDI{RS}")
                        logging.info("="*30)
                        print() # Add newline after successful login message
                        animated_interrupted = animated_sleep(1, "Oturum bilgileri aliniyor (ViewState)...", color=C)
                        if animated_interrupted or exit_requested: break # Check after sleep
                        last_view_state = get_initial_viewstate(session)
                        if not last_view_state:
                             logging.warning("Basarili giristen sonra ilk ViewState alinamadi. Kota kontrolu calismayabilir.")

                    elif login_result == "CREDENTIAL_ERROR":
                        credential_error_attempts += 1
                        # login_attempts += 1 # Also count as a general attempt
                        logging.warning(f"Hatali kullanici adi veya sifre tespit edildi (Deneme {credential_error_attempts}/{MAX_CREDENTIAL_ATTEMPTS}).")

                        if credential_error_attempts < MAX_CREDENTIAL_ATTEMPTS:
                             print(f"\n{R}--- HATALI GIRIS BILGISI ---{RS}")
                             print(f"{Y}Kayitli/Girilmis kullanici adi veya sifre yanlis gorunuyor.{RS}") # Modified message slightly
                             print(f"{Y}Kalan deneme hakkiniz: {MAX_CREDENTIAL_ATTEMPTS - credential_error_attempts}{RS}")
                             print(f"{M}--------------------------{RS}")
                             print(f"{M}1:{RS} Tekrar Dene (Mevcut bilgilerle)")
                             print(f"{M}2:{RS} Giris Bilgilerini Degistir")
                             print(f"{M}3:{RS} Programdan Cik")
                             print(f"{M}--------------------------{RS}")
                             retry_choice = input(f"{W}Seciminiz: {RS}").strip()
                             print() # Add newline after input

                             if retry_choice == '1':
                                 print(f"{C}Mevcut bilgilerle tekrar denenecek...{RS}")
                                 animated_interrupted = animated_sleep(3, "Tekrar deneniyor...", color=Y)
                                 if animated_interrupted or exit_requested: break
                                 session = requests.Session() # Reset session cookies for retry
                                 continue # Continue to next loop iteration to retry login
                             elif retry_choice == '2':
                                 session = handle_credential_change(session) # Refactored function
                                 credential_error_attempts = 0 # Reset counter after changing
                                 login_attempts = 0 # Reset general attempts too
                                 # State is reset inside handle_credential_change
                                 if exit_requested: break # Check flag after potential sleep in handler
                                 continue # Continue loop to attempt login with new credentials
                             elif retry_choice == '3':
                                 logging.info("Kullanici hatali giris sonrasi cikmayi secti.")
                                 print(f"{Y}Programdan cikiliyor...{RS}")
                                 exit_without_logout = True # Credentials were bad, no need to logout
                                 break
                             else: # This else should be aligned with the 'if retry_choice == ...'
                                 print(f"{R}Gecersiz secim. Tekrar deneyin.{RS}")
                                 animated_interrupted = animated_sleep(2, "Hatali secim...", color=R)
                                 if animated_interrupted or exit_requested: break
                                 continue # Go back to the credential error prompt
                        else: # This else should be aligned with 'if credential_error_attempts < ...'
                             logging.error(f"{MAX_CREDENTIAL_ATTEMPTS} kez hatali giris denemesi yapildi. Program durduruluyor.")
                             print(f"\n{R}Maksimum hatali giris deneme hakkina ulasildi.{RS}")
                             print(f"{R}Lutfen .env dosyasindaki bilgileri kontrol edin veya programi yeniden baslatip bilgileri degistirin.{RS}")
                             animated_interrupted = animated_sleep(8, "Kapatiliyor...", color=R)
                             exit_without_logout = True
                             break # Exit program

                    else: # login_result is False (Network or other error) - This else should be aligned with 'if login_result is True:'
                        logged_in = False # This block needs one more level of indentation
                        login_attempts += 1
                        credential_error_attempts = 0 # Reset credential error count on other failures
                        logging.warning(f"Giris basarisiz (Network/Sunucu Hatasi?). {RETRY_DELAY} saniye sonra tekrar denenecek ({login_attempts}/{MAX_LOGIN_ATTEMPTS})...")
                        print() # Add newline before retry sleep
                        animated_interrupted = animated_sleep(RETRY_DELAY, f"{RETRY_DELAY} sn sonra tekrar denenecek...", color=Y)
                        if animated_interrupted or exit_requested: break # Check after sleep
                        session = requests.Session() # Reset session fully on general errors
                        continue # Retry validation
                else:
                    logging.error(f"{MAX_LOGIN_ATTEMPTS} kez basarisiz genel giris denemesi yapildi (Network vb.). Program durduruluyor.")
                    print(f"\n{R}Sunucuya ulasilamiyor veya baska bir sorun var gibi gorunuyor.{RS}")
                    print(f"{R}Internet baglantinizi ve KYK WiFi'ye bagli oldugunuzu kontrol edin.{RS}")
                    animated_interrupted = animated_sleep(5, "Kapatiliyor...", color=R)
                    break # Exit program

            # --- Menu Asamasi --- #
            # Eger giris yapildiysa (either from initial validation or main loop login), kullaniciya menuyu goster.
            if logged_in:
                # Menuyu yazdir
                print(f"\n{BR}{M}--- Ana Menu ---{RS}")
                print(f"{BR}{C}1:{RS} Kalan Kotayı Göster")
                print(f"{BR}{C}2:{RS} Oturumu Açık Tut (Normal Mod - {AJAX_INTERVAL // 60} dk Kontrol)") # Show interval dynamically
                print(f"{BR}{C}3:{RS} Oturumu Açık Tut (Hızlı Mod - {FAST_AJAX_INTERVAL} sn Kontrol)") # Show interval dynamically
                print(f"{BR}{C}4:{RS} Giriş Bilgilerini Değiştir")
                print(f"{BR}{C}5:{RS} Oturumu Kapat ve Çık")
                print(f"{BR}{C}6:{RS} Programdan Çık (Oturum Açık Kalsın)")
                print(f"{BR}{M}---------------{RS}")
                print() # Add newline before prompt

                # Kullanicidan secim al
                choice = input(f"{W}Seciminiz (Varsayilan: 1 - Kalan Kotayı Göster): {RS}").strip()

                # Check if Ctrl+C was pressed during input
                if exit_requested:
                    logging.info("Ctrl+C detected during menu input. Resetting flag and showing menu.")
                    exit_requested = False
                    continue # Go back to the start of the main loop to show menu

                if not choice:
                    choice = '1' # Update default choice
                    print(f"-> {C}Varsayilan secenek '1' (Kalan Kotayı Göster) kullaniliyor.{RS}")

                # --- Secime Gore Islem --- #
                print() # Add newline after choice confirmation/input

                if choice == '1':
                    # --- Manuel Kota Kontrolu --- #
                    print(f"{M}{BR}--- Kota Bilgisi Sorgulama ---{RS}")
                    logging.info("Manuel kota bilgisi kontrol ediliyor...")
                    if not last_view_state:
                         animated_interrupted = animated_sleep(1, "ViewState aliniyor...", color=C)
                         if animated_interrupted or exit_requested: break
                         last_view_state = get_initial_viewstate(session)
                         if not last_view_state:
                             logging.error("Manuel kota sorgulamasi icin ViewState alinamadi.")
                             logged_in = False
                             session = requests.Session() # Reset session
                             continue # Go back to main loop start (will trigger login)

                    if exit_requested: break # Check before AJAX

                    animated_interrupted = animated_sleep(2, "Kota sorgulaniyor...", color=C)
                    if animated_interrupted or exit_requested: break

                    quota_info, new_view_state = get_quota_ajax(session, last_view_state)

                    if exit_requested: break # Check after AJAX

                    if quota_info == "SESSION_EXPIRED":
                         logging.error("Oturumun suresi dolmus gibi gorunuyor. Yeniden giris denenecek.")
                         logged_in = False
                         last_view_state = None
                         session = requests.Session()
                         continue

                    if quota_info:
                         quota_value_str = quota_info.get("Toplam Kalan Kota", "N/A")
                         print(f"{G}-> Kalan Kota: {quota_value_str}{RS}")
                         print() # Add newline after quota info
                    else:
                         logging.warning("-> Kota bilgisi alinamadi.")
                         print() # Add newline even if quota failed

                    if new_view_state:
                         last_view_state = new_view_state
                    else:
                         logging.warning("Manuel kontrol: AJAX yanitindan yeni ViewState alinamadi.")
                         last_view_state = None # Force refresh next time

                    print(f"{M}{BR}------------------------------{RS}")
                    # logging.info("-" * 30)
                    print() # Add newline before enter prompt
                    # input() will block, but signal handler should still set the flag
                    input(f"{Y}Devam etmek icin Enter tusuna basin...{RS}")
                    # Check if Ctrl+C was pressed during input
                    if exit_requested:
                        logging.info("Ctrl+C detected after 'Press Enter'. Resetting flag and showing menu.")
                        exit_requested = False
                        continue # Go back to the start of the main loop to show menu

                elif choice == '2':
                    # --- Oturumu Acik Tut Modu (Normal) --- #
                    logging.info("Oturumu acik tutma modu baslatiliyor...")
                    print(f"({Y}Bu moddan cikip menuye donmek icin Ctrl+C tusuna basin{RS})")
                    print() # Add newline after instruction
                    last_quota_check_time = 0
                    while True: # Oturumu acik tutma dongusu
                        if exit_requested:
                            logging.info("Exit requested flag detected during keep-alive mode.")
                            break # Exit inner keep-alive loop

                        current_time = time.time()
                        if current_time - last_quota_check_time >= AJAX_INTERVAL:
                            # Updated log message
                            logging.info(f"Oturum aktif tutuluyor (Normal Mod - Kontrol her {AJAX_INTERVAL // 60} dk)... ")
                            if not last_view_state:
                                logging.debug("Keep-alive icin ViewState aliniyor...")
                                animated_interrupted = animated_sleep(1, "ViewState aliniyor...", C)
                                if animated_interrupted or exit_requested: break # Check flag after sleep
                                last_view_state = get_initial_viewstate(session)
                                if not last_view_state:
                                    logging.error("ViewState alinamadi. Oturum hatasi olabilir. Menuye donuluyor.")
                                    logged_in = False
                                    session = requests.Session() # Reset session? Maybe just break.
                                    break # Break inner loop to re-evaluate login state

                            if exit_requested: break # Check flag before potentially long AJAX call

                            logging.debug("Keep-alive: Kota sorgulaniyor...")
                            # Consider adding a short sleep/yield here if get_quota_ajax is very fast
                            # time.sleep(0.01)
                            quota_info, new_view_state = get_quota_ajax(session, last_view_state)

                            if exit_requested: break # Check flag immediately after AJAX call

                            if quota_info == "SESSION_EXPIRED":
                                logging.error("Oturumun suresi dolmus gibi gorunuyor. Yeniden giris denenecek.")
                                logged_in = False
                                last_view_state = None
                                session = requests.Session()
                                break # Break inner loop to re-login

                            if quota_info:
                                quota_value_str = quota_info.get("Toplam Kalan Kota", "N/A")
                                logger.info(f"Kalan Kota: {quota_value_str}")
                                print() # Add newline after quota info
                            else:
                                # Allow continuing if quota fails but ViewState might be ok
                                logging.warning("-> Kota bilgisi (Keep-Alive) alinamadi.")
                                print() # Add newline even if quota failed

                            if new_view_state:
                                if new_view_state != last_view_state:
                                    logging.debug("Keep-alive: ViewState guncellendi.")
                                    last_view_state = new_view_state
                                else:
                                    logging.debug("Keep-alive: ViewState degismedi.")
                            else:
                                logging.warning("Keep-alive: AJAX yanitindan yeni ViewState alinamadi. Sonraki kontrol ViewState'i yeniden almayi deneyecek.")
                                last_view_state = None # Force refresh next time

                            last_quota_check_time = current_time

                        # Check flag again before sleeping
                        if exit_requested:
                            logging.info("Exit requested flag detected before sleep in keep-alive.")
                            break

                        # Calculate sleep duration and call modified animated_sleep
                        time_since_last_check = time.time() - last_quota_check_time
                        # Ensure sleep_duration is never negative if checks take too long
                        sleep_duration = max(0.5, AJAX_INTERVAL - time_since_last_check)
                        logging.debug(f"Keep-alive: Sonraki kontrol icin {sleep_duration:.1f} saniye bekleniyor...")
                        # Updated animated sleep message
                        interrupted = animated_sleep(sleep_duration, "Sonraki oturum kontrolu bekleniyor...", color=C)

                        # Check if sleep was interrupted OR if flag was set during quota check
                        if interrupted or exit_requested:
                            logging.info("Oturumu Acik Tut modu Ctrl+C ile durduruldu. Ana menuye donuluyor.")
                            print() # Add newline before showing menu again
                            # Reset the flag so the main loop continues instead of exiting
                            exit_requested = False
                            break # Exit inner keep-alive loop

                    # After the inner loop breaks
                    if not logged_in: # If loop broke due to session issue, don't log this
                        logging.info("Keep-alive mode stopped (likely session issue). Returning to main loop.")
                        print() # Add newline

                elif choice == '3':
                    # --- Sürekli Oturumu Acik Tut Modu (Hizli) --- #
                    logging.info("Sürekli oturumu acik tutma modu (Hızli) baslatiliyor...")
                    print(f"({Y}Bu moddan cikip menuye donmek icin Ctrl+C tusuna basin{RS})")
                    print() # Add newline after instruction
                    last_quota_check_time = 0
                    while True: # Hizli oturumu acik tutma dongusu
                        if exit_requested:
                            logging.info("Exit requested flag detected during fast keep-alive mode.")
                            break # Exit inner fast keep-alive loop

                        current_time = time.time()
                        # Use FAST_AJAX_INTERVAL here
                        if current_time - last_quota_check_time >= FAST_AJAX_INTERVAL:
                             # Updated log message
                            logging.info(f"Oturum aktif tutuluyor (Hizli Mod - Kontrol her {FAST_AJAX_INTERVAL} sn)... ")
                            if not last_view_state:
                                logging.debug("Fast Keep-alive icin ViewState aliniyor...")
                                animated_interrupted = animated_sleep(1, "ViewState aliniyor...", C)
                                if animated_interrupted or exit_requested: break # Check flag after sleep
                                last_view_state = get_initial_viewstate(session)
                                if not last_view_state:
                                    logging.error("ViewState alinamadi. Oturum hatasi olabilir. Menuye donuluyor.")
                                    logged_in = False
                                    session = requests.Session()
                                    break # Break inner loop to re-evaluate login state

                            if exit_requested: break # Check flag before potentially long AJAX call

                            logging.debug("Fast Keep-alive: Kota sorgulaniyor...")
                            quota_info, new_view_state = get_quota_ajax(session, last_view_state)

                            if exit_requested: break # Check flag immediately after AJAX call

                            if quota_info == "SESSION_EXPIRED":
                                logging.error("Oturumun suresi dolmus gibi gorunuyor. Yeniden giris denenecek.")
                                logged_in = False
                                last_view_state = None
                                session = requests.Session()
                                break # Break inner loop to re-login

                            if quota_info:
                                # Quota info received, but we don't display it in fast mode
                                # quota_value_str = quota_info.get("Toplam Kalan Kota", "N/A")
                                # logger.info(f"Kalan Kota: {quota_value_str}")
                                # print() # Add newline after quota info
                                pass # Explicitly do nothing with the quota info
                            else:
                                logging.warning("-> Kota bilgisi (Fast Keep-Alive) alinamadi.")
                                print() # Add newline even if quota failed

                            if new_view_state:
                                if new_view_state != last_view_state:
                                    logging.debug("Fast Keep-alive: ViewState guncellendi.")
                                    last_view_state = new_view_state
                                else:
                                    logging.debug("Fast Keep-alive: ViewState degismedi.")
                            else:
                                logging.warning("Fast Keep-alive: AJAX yanitindan yeni ViewState alinamadi. Sonraki kontrol ViewState'i yeniden almayi deneyecek.")
                                last_view_state = None # Force refresh next time

                            last_quota_check_time = current_time

                        # Check flag again before sleeping
                        if exit_requested:
                            logging.info("Exit requested flag detected before sleep in fast keep-alive.")
                            break

                        # Calculate sleep duration and call modified animated_sleep
                        time_since_last_check = time.time() - last_quota_check_time
                        # Use FAST_AJAX_INTERVAL here
                        sleep_duration = max(0.5, FAST_AJAX_INTERVAL - time_since_last_check)
                        logging.debug(f"Fast Keep-alive: Sonraki kontrol icin {sleep_duration:.1f} saniye bekleniyor...")
                        # Updated animated sleep message
                        interrupted = animated_sleep(sleep_duration, "Sonraki hizli oturum kontrolu bekleniyor...", color=C)

                        # Check if sleep was interrupted OR if flag was set during quota check
                        if interrupted or exit_requested:
                            logging.info("Hizli Oturumu Acik Tut modu Ctrl+C ile durduruldu. Ana menuye donuluyor.")
                            print() # Add newline before showing menu again
                            # Reset the flag so the main loop continues instead of exiting
                            exit_requested = False
                            break # Exit inner fast keep-alive loop

                    # After the inner loop breaks
                    if not logged_in: # If loop broke due to session issue, don't log this
                         logging.info("Fast Keep-alive mode stopped (likely session issue). Returning to main loop.")
                         print() # Add newline - This print should be aligned with the logging call above it

                elif choice == '4': # Was Change Credentials (5)
                    # --- Giris Bilgilerini Degistir (Menu Secenegi) --- #
                    # handle_credential_change adds its own spacing
                    session = handle_credential_change(session) # Call refactored function
                    # State (logged_in, attempts, etc.) is reset inside the function
                    if exit_requested: break # Check flag set during interaction
                    continue # Go back to the start of the loop to attempt login with new creds

                elif choice == '5': # Was Logout (2)
                    # --- Oturumu Kapat --- #
                    print() # Add newline before starting
                    logging.info("Oturum kapatiliyor...")
                    jsessionid_to_logout = session.cookies.get('JSESSIONID')
                    if not jsessionid_to_logout:
                        try:
                            if SESSION_FILE_PATH.exists():
                                jsessionid_to_logout = SESSION_FILE_PATH.read_text(encoding="utf-8").strip()
                        except Exception as e_read:
                            logging.error(f"{SESSION_FILE_PATH} dosyasi logout icin okunurken hata: {e_read}", exc_info=False)
                            logging.debug("Oturum dosyasi okuma hatasi (Logout):", exc_info=True)

                    if jsessionid_to_logout:
                        animated_interrupted = animated_sleep(2, "Oturum kapatiliyor...", color=Y)
                        # If interrupted during logout sleep, just break. Finally block handles cleanup.
                        if animated_interrupted or exit_requested: break

                        if perform_logout(jsessionid_to_logout):
                            logging.info("Oturum basariyla kapatildi.")
                        else:
                            logging.warning("Oturum kapatilamadi veya kapatma durumu dogrulanamadi.")
                    else:
                        logging.warning("Kapatilacak aktif oturum kimligi (JSESSIONID) bulunamadi.")

                    logged_in = False
                    last_view_state = None
                    session = requests.Session()
                    login_attempts = 0
                    logging.info("Oturum kapatildi. Programdan cikiliyor...")
                    exit_without_logout = True # Prevent finally block from trying logout again
                    break

                elif choice == '6': # Was Exit Program (4)
                    # --- Programdan Cik --- #
                    logging.info("Programdan cikiliyor (Oturum kapatilmayacak)...")
                    exit_without_logout = True # Prevent finally block logout
                    break # Ana donguyu sonlandir

                else: # Corrected indentation
                    # Gecersiz secim durumu
                    print(f"{R}Gecersiz secim: '{choice}'. Lutfen 1, 2, 3, 4, 5 veya 6 girin.{RS}") # Update error message range
                    animated_interrupted = animated_sleep(1.5, "Hatali secim...", color=R)
                    if animated_interrupted or exit_requested: break

            # Check flag at the end of the main loop iteration too
            if exit_requested:
                 logging.info("Exit requested flag detected at main loop end.")
                 break

    except KeyboardInterrupt:
        logging.warning("Program kullanici tarafindan manuel olarak durduruldu (KeyboardInterrupt).")
        # Flag should be set by handler, but ensure exit_without_logout logic runs
        if not exit_requested:
            # If handler didn't run for some reason, log and set flag
            logging.warning("KeyboardInterrupt yakalandi ama exit_requested bayragi set edilmemis gorunuyor. Manuel set ediliyor.")
            exit_requested = True # Ensure finally block behaves correctly

    except Exception as e:
        # Beklenmedik bir hata olusursa
        logging.error(f"\nAna dongude beklenmeyen bir hata olustu.", exc_info=False)
        logging.debug("Ana dongu hatasi detaylari:", exc_info=True)
    finally:
        # --- Program Kapanis Islemleri --- #
        logging.info("Executing finally block...")
        # Programdan cikarken oturumu (gerekiyorsa) kapatir ve gecici dosyalari temizler.
        if logged_in and 'session' in locals() and session and not exit_without_logout:
             logging.info("Program kapatiliyor. Acik oturum kapatilmaya calisiliyor...")
             jsessionid_to_logout = session.cookies.get('JSESSIONID')
             if not jsessionid_to_logout:
                  try:
                      if SESSION_FILE_PATH.exists():
                           jsessionid_to_logout = SESSION_FILE_PATH.read_text(encoding="utf-8").strip()
                  except Exception as e_final_read:
                       logging.warning(f"{SESSION_FILE_PATH} dosyasi finalde okunurken hata: {e_final_read}")

             if jsessionid_to_logout:
                 if perform_logout(jsessionid_to_logout):
                     logging.info("Oturum cikista basariyla kapatildi.")
                 else:
                     logging.warning("Oturum cikista kapatilamadi veya durum dogrulanamadi.")
             else:
                 logging.warning("Cikista kapatilacak aktif oturum kimligi (JSESSIONID) bulunamadi.")
        else:
             if exit_without_logout:
                  logging.info("Program kapatiliyor (Kullanici istegiyle oturum acik birakildi).")
             else:
                  logging.info("Program kapatiliyor (Oturum acik degildi veya zaten kapatilmisti).")

        if not exit_without_logout:
             try:
                  if SESSION_FILE_PATH.exists():
                       SESSION_FILE_PATH.unlink()
                       logging.debug(f"Cikista oturum bilgi dosyasi ({SESSION_FILE_PATH}) temizlendi.")
             except OSError as e:
                  logging.warning(f"Cikista oturum bilgi dosyasi ({SESSION_FILE_PATH}) silinirken hata: {e}", exc_info=False)
                  logging.debug("Oturum dosyasi silme hatasi (Finally):", exc_info=True)
        else:
            logging.debug(f"Oturum bilgi dosyasi ({SESSION_FILE_PATH}) bilerek silinmedi.")

        logging.info("Program sonlandi.")

#
#         _     
#   ___  | |__  
#  / _ \_| / /_ 
#  \___(_)_/'(_) 
#               
#