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
        print("⚠️ Telegram não configurado nos Secrets. Pulando notificação.")
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
            url_api_msg = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload_msg = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": mensagem,
                "parse_mode": "HTML",
                "disable_web_page_preview": False
            }
            res = requests.post(url_api_msg, json=payload_msg)

        if res.status_code == 200:
            print(f"📢 Notificação enviada para o Telegram: {nome_jogo} ({versao_jogo})")
        else:
            print(f"❌ Erro ao enviar Telegram: {res.text}")
    except Exception as e:
        print(f"❌ Erro na API do Telegram: {e}")

def enviar_notificacao_whatsapp(nome_jogo, versao_jogo, id_jogo):
    if not GREEN_API_INSTANCE or not GREEN_API_TOKEN or not GREEN_API_GROUP_ID:
        print("⚠️ GREEN-API não configurada nos Secrets. Pulando WhatsApp.")
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

        if res.status_code == 200:
            print(f"🟢 Notificação enviada com sucesso para o WhatsApp: {nome_jogo} ({versao_jogo})")
    except Exception as e:
        print(f"❌ Erro na API do WhatsApp: {e}")

def buscar_dados_atuais_firebase(id_jogo):
    firebase_base_url = "https://meublog-apks-default-rtdb.firebaseio.com"
    try:
        res = requests.get(f"{firebase_base_url}/links/{id_jogo}.json")
        if res.status_code == 200 and res.text != 'null':
            return res.json()
    except Exception as e:
        print(f"Erro ao consultar Firebase: {e}")
    return {}

def extrair_id_jogo(url_origem):
    """Extrai o ID limpo ignorando categorias, parâmetros e versões."""
    url_limpa = url_origem.split(']')[0].split('?')[0].rstrip('/')
    partes = [p for p in url_limpa.split('/') if p]
    
    ignorar = {
        'http:', 'https:', '24hmod.com', 'apkvision.org', 'modyolo.com', 'modplays.com',
        'download', 'file', 'games', 'action', 'racing', 'simulation', 'arcade', 
        'sports', 'casual', 'strategy', 'role-playing', 'adventure'
    }
    
    partes_validas = []
    for p in partes:
        p_lower = p.lower()
        if p_lower in ignorar or p_lower.isdigit():
            continue
        if re.match(r'^v?\d+[\.\-]\d+', p_lower):
            continue
        partes_validas.append(p)
        
    if partes_validas:
        id_jogo = partes_validas[-1]
    else:
        id_jogo = "jogo"
        
    id_jogo = re.sub(r'-apk-\d+.*$', '', id_jogo, flags=re.IGNORECASE)
    id_jogo = re.sub(r'-\d+$', '', id_jogo)
    id_jogo = re.sub(r'-(?:apk|mod)$', '', id_jogo, flags=re.IGNORECASE)
    id_jogo = id_jogo.replace('.html', '').replace('.apk', '')
    
    return id_jogo

def extrair_versao_limpa(texto_ou_url):
    """Extrai uma versão válida (ex: v0.4.8) ignorando números de scripts e anos."""
    if not texto_ou_url:
        return None

    # Normaliza separadores no formato 0-4-8 para 0.4.8
    texto = re.sub(r'(\d+)-(\d+)-(\d+)', r'\1.\2.\3', texto_ou_url)
    texto = re.sub(r'(\d+)-(\d+)', r'\1.\2', texto)

    candidatos = re.findall(r'\bv?(\d+\.\d+(?:\.\d+)?)\b', texto, re.IGNORECASE)
    
    for c in candidatos:
        partes = c.split('.')
        if len(partes) >= 2:
            try:
                major = int(partes[0])
                # Descarta anos (ex: 2024, 2025, 2026...)
                if len(partes[0]) == 4 and major >= 2000:
                    continue
                # Versões de jogos dificilmente têm o primeiro número maior que 100
                if major > 100:
                    continue
                return f"v{c}"
            except ValueError:
                continue
    return None

def limpar_nome_jogo(raw_title, url_alvo):
    """Limpa o título removendo palavras de ação, marcas, versão e palavra Download em qualquer posição."""
    if not raw_title:
        id_limpo = extrair_id_jogo(url_alvo)
        return id_limpo.replace('-', ' ').title()

    nome = raw_title
    # Remove marcas e domínios
    nome = re.sub(r'(?:24hmod\.com|24hmod|apkvision\.org|apkvision)\b', '', nome, flags=re.IGNORECASE)
    # Remove palavras desnecessárias em QUALQUER lugar do texto
    nome = re.sub(r'\b(?:Download|Baixar|Free|MOD|APK|XAPK|Unlimited|Coins|Money|Android)\b', '', nome, flags=re.IGNORECASE)
    # Remove a versão numérica do nome
    nome = re.sub(r'\bv?\d+[\.\-]\d+(?:[\.\-]\d+)*\b', '', nome, flags=re.IGNORECASE)
    # Remove parênteses e colchetes
    nome = re.sub(r'\([^)]*\)|\[[^\]]*\]', '', nome)
    # Limpa espaços duplos e caracteres especiais nas bordas
    nome = re.sub(r'[\s\-–|:]+', ' ', nome).strip()

    if not nome or len(nome) < 2:
        id_limpo = extrair_id_jogo(url_alvo)
        return id_limpo.replace('-', ' ').title()

    return nome

def salvar_no_firebase_se_novo(url_origem, link_novo, dados_jogo):
    id_jogo = extrair_id_jogo(url_origem)

    nome_jogo = dados_jogo.get("nome", id_jogo.replace('-', ' ').title())
    versao_jogo = dados_jogo.get("versao", "Última Versão")
    foto_url = FOTO_OFICIAL_SITE

    dados_atuais = buscar_dados_atuais_firebase(id_jogo)
    versao_atual = dados_atuais.get("versao") if isinstance(dados_atuais, dict) else None

    # 1. Atualiza SEMPRE os links no Firebase silenciosamente
    firebase_base_url = "https://meublog-apks-default-rtdb.firebaseio.com"
    payload = {
        "url_original": url_origem,
        "link_direto": link_novo,
        "nome": nome_jogo,
        "versao": versao_jogo,
        "foto": foto_url
    }

    try:
        requests.patch(f"{firebase_base_url}/links/{id_jogo}.json", json=payload)
        requests.patch(f"{firebase_base_url}/jogos/{id_jogo}.json", json=payload)
        print(f"✅ Firebase atualizado para '{id_jogo}' ({versao_jogo}).")
    except Exception as e:
        print(f"❌ Erro ao salvar no Firebase: {e}")

    # 2. REGRA ESTRITA DE NOTIFICAÇÃO:
    # Só dispara para o Telegram e WhatsApp se a VERSÃO for diferente da gravada no Firebase
    if versao_atual and versao_atual.strip().lower() == versao_jogo.strip().lower():
        print(f"⏩ Notificação ignorada: A versão de '{id_jogo}' continua a mesma ({versao_jogo}).")
    else:
        print(f"🔔 VERSÃO MUDOU para '{id_jogo}' ({versao_atual} ➔ {versao_jogo})! Enviando notificações...")
        enviar_notificacao_telegram(nome_jogo, versao_jogo, id_jogo)
        enviar_notificacao_whatsapp(nome_jogo, versao_jogo, id_jogo)

    return id_jogo

def extrair_link_direto(url_alvo):
    print(f"Iniciando extração para: {url_alvo}")

    dados_jogo = {
        "nome": "Jogo Desconhecido",
        "versao": "Última Versão",
        "foto": FOTO_OFICIAL_SITE
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-size=375,812',
            ]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            viewport={"width": 375, "height": 812},
            is_mobile=True,
            has_touch=True,
            locale="pt-BR",
            accept_downloads=True
        )

        page = context.new_page()

        if stealth_sync:
            stealth_sync(page)
        else:
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

        link_final = None

        def interceptar_requisicao(request):
            nonlocal link_final
            url = request.url

            ignorar_dominios = [
                "yandex", "mc.yandex", "google-analytics", "googletagmanager", 
                "facebook", "doubleclick", "cdn-cgi", "challenge-platform"
            ]
            if any(dom in url for dom in ignorar_dominios):
                return

            if not url.startswith("blob:") and "play.google.com" not in url:
                if "dl.24hmod.com" in url or "file.24hmod.com" in url or "file.apkvision.org" in url or "downloads.apkvision.org" in url:
                    link_final = url
                elif (url.endswith(".apk") or url.endswith(".xapk") or ".apk?" in url or ".xapk?" in url) and "apkvision.org/games" not in url:
                    link_final = url

        page.on("request", interceptar_requisicao)

        try:
            page.goto(url_alvo, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)

            # Captura elementos do DOM
            h1_text = ""
            try:
                if page.locator("h1").count() > 0:
                    h1_text = page.locator("h1").first.inner_text() or ""
            except:
                pass

            page_title = page.title() or ""

            og_title = ""
            try:
                og_elem = page.locator('meta[property="og:title"]').first
                if og_elem.count() > 0:
                    og_title = og_elem.get_attribute("content") or ""
            except:
                pass

            # 1. EXTRAÇÃO DE VERSÃO (URL -> H1 -> Title)
            versao_encontrada = (
                extrair_versao_limpa(url_alvo) or 
                extrair_versao_limpa(h1_text) or 
                extrair_versao_limpa(og_title) or 
                extrair_versao_limpa(page_title)
            )
            if versao_encontrada:
                dados_jogo["versao"] = versao_encontrada

            # 2. EXTRAÇÃO DE NOME
            raw_title = h1_text or og_title or page_title
            dados_jogo["nome"] = limpar_nome_jogo(raw_title, url_alvo)

            # FLUXO 1: 24HMOD.COM
            if "24hmod.com" in url_alvo:
                print("⏳ Aguardando contador e botões do 24hmod...")
                page.wait_for_timeout(9000)
                botoes = page.locator("a, button").all()
                for b in botoes:
                    try:
                        texto = (b.inner_text() or "").lower()
                        href = b.get_attribute("href") or ""
                        if ("download" in texto or "dl.24hmod.com" in href) and "play.google.com" not in href:
                            if "dl.24hmod.com" in href or href.endswith(".apk"):
                                link_final = href
                                break
                            b.click(force=True, timeout=4000)
                            page.wait_for_timeout(5000)
                            break
                    except:
                        continue

            # FLUXO 2: APKVISION.ORG
            elif "apkvision.org" in url_alvo:
                print("⏳ Iniciando fluxo do Apkvision...")
                if "/download/" not in page.url:
                    btn_dl = page.locator("a.btn-download, a[href*='/download/']").first
                    if btn_dl.count() > 0:
                        btn_dl.click(force=True)
                        page.wait_for_timeout(4000)

                print("⏳ Aguardando contador do Apkvision (10s)...")
                page.wait_for_timeout(10000)

                btn_final = page.locator("a.btn-file, a[href*='file.apkvision.org'], a[href*='downloads.apkvision.org']").first
                if btn_final.count() > 0:
                    href = btn_final.get_attribute("href")
                    if href and ("file.apkvision.org" in href or "downloads.apkvision.org" in href or ".apk" in href or ".xapk" in href):
                        link_final = href
                    else:
                        btn_final.click(force=True)
                        page.wait_for_timeout(5000)

            # Varredura final no DOM
            if not link_final:
                hrefs = page.eval_on_selector_all("a[href]", "elements => elements.map(e => e.href)")
                for href in hrefs:
                    if "yandex" not in href and "cdn-cgi" not in href and not href.startswith("blob:"):
                        if any(k in href for k in ["dl.24hmod.com", "file.24hmod.com", "file.apkvision.org", "downloads.apkvision.org"]):
                            link_final = href
                            break
                        elif (href.endswith(".apk") or href.endswith(".xapk")) and "apkvision.org/games" not in href:
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
    print(f"\n==================================================")
    link, dados_jogo = extrair_link_direto(url_alvo)
    if link:
        id_jogo = salvar_no_firebase_se_novo(url_alvo, link, dados_jogo)
        salvar_url_na_lista(url_alvo)
        link_protegido = f"{URL_WORKER}?id={id_jogo}"
        print(f"LINK_ENCONTRADO:{link_protegido}")
    else:
        print(f"❌ Nenhum link direto encontrado para: {url_alvo}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].strip():
        raw_input = sys.argv[1]
        urls_encontradas = re.findall(r'https?://[^\s,]+', raw_input)
        
        if urls_encontradas:
            for url in urls_encontradas:
                processar_jogo(url.strip())
        else:
            processar_jogo(raw_input.strip())
    else:
        arquivo_jogos = "jogos.txt"
        if os.path.exists(arquivo_jogos):
            with open(arquivo_jogos, "r", encoding="utf-8") as f:
                lista_urls = [linha.strip() for linha in f if linha.strip()]
            
            print(f"🤖 Rodando em modo automático. {len(lista_urls)} jogo(s) para verificar...")
            for url in lista_urls:
                processar_jogo(url)
        else:
            print("⚠️ Nenhuma URL cadastrada no 'jogos.txt'. Adicione uma URL manualmente primeiro.")
