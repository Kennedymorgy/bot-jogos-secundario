import sys
import os
import re
import requests
from playwright.sync_api import sync_playwright

try:
    from playwright_stealth import stealth_sync
except ImportError:
    stealth_sync = None

# Secrets do GitHub
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

GREEN_API_INSTANCE = os.environ.get("GREEN_API_INSTANCE")
GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN")
GREEN_API_GROUP_ID = os.environ.get("GREEN_API_GROUP_ID")

URL_WORKER = "https://orange-star-d066.claudiokennedymorgy.workers.dev"
PAGINA_INICIAL_BLOG = "https://k-404modapk.blogspot.com/?m=1"
FOTO_OFICIAL_SITE = "https://k-404modapk.blogspot.com/favicon.ico"

def enviar_notificacao_telegram(nome_jogo, versao_jogo, id_jogo):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    mensagem = (
        f"🔥 <b>JOGO ATUALIZADO!</b>\n\n"
        f"🎮 <b>Jogo:</b> {nome_jogo}\n"
        f"📦 <b>Versão:</b> {versao_jogo}\n"
        f"🔗 <b>Página:</b> <a href='{PAGINA_INICIAL_BLOG}'>Baixar no Blog</a>\n\n"
        f"⚡ <i>Nova versão disponível no servidor! Atualize os dados no Blogger se necessário.</i>"
    )

    url_api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": FOTO_OFICIAL_SITE,
        "caption": mensagem,
        "parse_mode": "HTML"
    }

    try:
        res = requests.post(url_api, json=payload)
        if res.status_code != 200:
            url_msg = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url_msg, json={"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "HTML"})
        print(f"📢 Notificação Telegram enviada: {nome_jogo} ({versao_jogo})")
    except Exception as e:
        print(f"❌ Erro Telegram: {e}")

def enviar_notificacao_whatsapp(nome_jogo, versao_jogo, id_jogo):
    if not GREEN_API_INSTANCE or not GREEN_API_TOKEN or not GREEN_API_GROUP_ID:
        return

    chat_id = GREEN_API_GROUP_ID.strip()
    if not chat_id.endswith("@g.us") and not chat_id.endswith("@c.us"):
        chat_id = f"{chat_id}@g.us"

    mensagem = (
        f"🔥 *JOGO ATUALIZADO!*\n\n"
        f"🎮 *Jogo:* {nome_jogo}\n"
        f"📦 *Versão:* {versao_jogo}\n"
        f"🔗 *Página:* {PAGINA_INICIAL_BLOG}\n\n"
        f"⚡ _Nova versão disponível no servidor! Atualize os dados no Blogger se necessário._"
    )

    url_file = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendFileByUrl/{GREEN_API_TOKEN}"
    payload_file = {
        "chatId": chat_id,
        "urlFile": FOTO_OFICIAL_SITE,
        "fileName": "icon.ico",
        "caption": mensagem
    }

    try:
        res = requests.post(url_file, json=payload_file)
        if res.status_code != 200:
            url_msg = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE}/sendMessage/{GREEN_API_TOKEN}"
            requests.post(url_msg, json={"chatId": chat_id, "message": mensagem})
        print(f"🟢 Notificação WhatsApp enviada: {nome_jogo} ({versao_jogo})")
    except Exception as e:
        print(f"❌ Erro WhatsApp: {e}")

def buscar_dados_atuais_firebase(id_jogo):
    firebase_base_url = "https://meublog-apks-default-rtdb.firebaseio.com"
    try:
        res = requests.get(f"{firebase_base_url}/links/{id_jogo}.json")
        if res.status_code == 200 and res.text != 'null':
            return res.json()
    except Exception as e:
        print(f"Erro Firebase: {e}")
    return {}

def extrair_id_jogo(url_origem):
    url_limpa = url_origem.split(']')[0].rstrip('/')
    partes = url_limpa.split('/')
    partes_filtradas = [p for p in partes if p and p not in ['download', 'file', 'games', 'action', 'racing', 'simulation'] and not p.isdigit()]
    
    id_jogo = partes_filtradas[-1] if partes_filtradas else "jogo"
    id_jogo = re.sub(r'-(?:apk|mod)?-\d+.*$', '', id_jogo, flags=re.IGNORECASE)
    id_jogo = id_jogo.replace('.html', '').replace('.apk', '')
    return id_jogo

def salvar_no_firebase_se_novo(url_origem, link_novo, dados_jogo):
    id_jogo = extrair_id_jogo(url_origem)
    nome_jogo = dados_jogo.get("nome", id_jogo.replace('-', ' ').title())
    versao_jogo = dados_jogo.get("versao", "Última Versão")

    dados_atuais = buscar_dados_atuais_firebase(id_jogo)
    link_atual = dados_atuais.get("link_direto") if isinstance(dados_atuais, dict) else None
    versao_atual = dados_atuais.get("versao") if isinstance(dados_atuais, dict) else None

    if link_atual == link_novo and versao_atual == versao_jogo:
        print(f"⏩ Jogo '{id_jogo}' sem alterações ({versao_jogo}).")
        return id_jogo

    print(f"🔄 Atualizando '{id_jogo}' no Firebase...")
    firebase_base_url = "https://meublog-apks-default-rtdb.firebaseio.com"
    payload = {
        "url_original": url_origem,
        "link_direto": link_novo,
        "nome": nome_jogo,
        "versao": versao_jogo,
        "foto": FOTO_OFICIAL_SITE
    }

    try:
        r1 = requests.patch(f"{firebase_base_url}/links/{id_jogo}.json", json=payload)
        requests.patch(f"{firebase_base_url}/jogos/{id_jogo}.json", json=payload)
        if r1.status_code == 200:
            print(f"✅ Firebase atualizado para: {id_jogo}")
            enviar_notificacao_telegram(nome_jogo, versao_jogo, id_jogo)
            enviar_notificacao_whatsapp(nome_jogo, versao_jogo, id_jogo)
    except Exception as e:
        print(f"❌ Erro ao salvar no Firebase: {e}")

    return id_jogo

def extrair_link_direto(url_alvo):
    print(f"\nIniciando extração para: {url_alvo}")
    dados_jogo = {"nome": "Jogo Desconhecido", "versao": "Última Versão", "foto": FOTO_OFICIAL_SITE}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox', '--disable-setuid-sandbox']
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            viewport={"width": 375, "height": 812},
            is_mobile=True,
            has_touch=True,
            locale="pt-BR"
        )

        page = context.new_page()

        if stealth_sync:
            stealth_sync(page)

        link_final = None

        def interceptar_requisicao(request):
            nonlocal link_final
            url = request.url
            
            ignorar = ["yandex", "google", "facebook", "doubleclick", "cdn-cgi", "analytics"]
            if any(i in url for i in ignorar):
                return

            if url.endswith(".apk") or url.endswith(".xapk") or ".apk?" in url or ".xapk?" in url:
                link_final = url
            elif "dl.24hmod.com" in url or "file.apkvision.org" in url or "downloads.apkvision.org" in url:
                link_final = url

        page.on("request", interceptar_requisicao)

        try:
            page.goto(url_alvo, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)

            full_title = ""
            og_title = page.locator('meta[property="og:title"]').first
            if og_title.count() > 0:
                full_title = og_title.get_attribute("content") or ""
            if not full_title:
                full_title = page.title()

            match_v = re.search(r'(?:v|ver|version)?\s*(\d+\.\d+(?:\.\d+)*)', full_title, re.IGNORECASE)
            if match_v:
                dados_jogo["versao"] = f"v{match_v.group(1)}"

            nome_limpo = re.split(r'\s+(?:MOD|v?\d+\.\d+|\(|-|–|Download|APK|XAPK)', full_title, flags=re.IGNORECASE)[0].strip()
            nome_limpo = re.sub(r'24hmod\.com|24hmod|apkvision\.org|apkvision', '', nome_limpo, flags=re.IGNORECASE).strip()

            if nome_limpo and len(nome_limpo) > 1:
                dados_jogo["nome"] = nome_limpo
            else:
                id_limpo = extrair_id_jogo(url_alvo)
                dados_jogo["nome"] = id_limpo.replace('-', ' ').title()

            if "24hmod.com" in url_alvo:
                print("Detectado site 24hmod.com, aguardando barra de progresso...")
                page.wait_for_timeout(10000)

                btn_now = page.locator("a:has-text('Download Now'), button:has-text('Download Now')").first
                if btn_now.count() > 0:
                    btn_now.click(force=True)
                    print("Botão 'Download Now' clicado!")
                    page.wait_for_timeout(5000)

            elif "apkvision.org" in url_alvo:
                print("Detectado site Apkvision.org...")

                btn_mod = page.locator("a.btn-download, a[href*='/download/']").first
                if btn_mod.count() > 0 and "/download/" not in page.url:
                    print("Clicando no botão de MOD do Apkvision...")
                    btn_mod.click(force=True)
                    page.wait_for_timeout(5000)

                print("Aguardando timer final do Apkvision...")
                page.wait_for_timeout(7000)

                btn_final = page.locator("a[href*='.apk'], a[href*='.xapk'], a.btn-file").first
                if btn_final.count() > 0:
                    href = btn_final.get_attribute("href")
                    if href and ("http" in href or ".apk" in href or ".xapk" in href):
                        link_final = href
                    else:
                        btn_final.click(force=True)
                        page.wait_for_timeout(5000)

            if not link_final:
                hrefs = page.eval_on_selector_all("a[href]", "elements => elements.map(e => e.href)")
                for href in hrefs:
                    if "yandex" not in href and "cdn-cgi" not in href:
                        if href.endswith(".apk") or href.endswith(".xapk") or "dl.24hmod.com" in href or "apkvision.org/file" in href:
                            link_final = href
                            break

        except Exception as e:
            print(f"Erro na navegação: {e}")

        browser.close()
        return link_final, dados_jogo

def salvar_url_na_lista(url):
    arquivo = "jogos.txt"
    urls_existentes = set()
    
    if os.path.exists(arquivo):
        with open(arquivo, "r", encoding="utf-8") as f:
            urls_existentes = set(line.strip() for line in f if line.strip())

    if url not in urls_existentes:
        with open(arquivo, "a", encoding="utf-8") as f:
            f.write(f"{url}\n")
        print(f"📝 URL salva em {arquivo} para monitoramento automático.")

def processar_jogo(url_alvo):
    link, dados_jogo = extrair_link_direto(url_alvo)
    if link:
        id_jogo = salvar_no_firebase_se_novo(url_alvo, link, dados_jogo)
        salvar_url_na_lista(url_alvo)
        link_protegido = f"{URL_WORKER}?id={id_jogo}"
        print(f"LINK_ENCONTRADO:{link_protegido}")
    else:
        print(f"❌ Nenhum link direto encontrado para: {url_alvo}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].startswith("http"):
        url_single = sys.argv[1]
        processar_jogo(url_single)
    else:
        arquivo_jogos = "jogos.txt"
        if os.path.exists(arquivo_jogos):
            with open(arquivo_jogos, "r", encoding="utf-8") as f:
                lista_urls = [linha.strip() for linha in f if linha.strip()]
            
            print(f"🤖 Rodando Bot Secundário. {len(lista_urls)} jogo(s) para verificar...")
            for url in lista_urls:
                processar_jogo(url)
        else:
            print("⚠️ Nenhuma URL salva no 'jogos.txt'.")
