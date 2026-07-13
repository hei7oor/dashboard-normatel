"""
Persiste dados no próprio repositório do GitHub via commit (API REST de Contents),
sem precisar de `git` instalado nem de banco de dados externo. Usado para o CSV de
respostas manuais e para o histórico diário de KPIs.
"""
import base64
import csv
import io
import time
import requests

REPO_PADRAO   = "hei7oor/dashboard-normatel"
BRANCH_PADRAO = "master"
API_BASE      = "https://api.github.com"


def _headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def baixar_arquivo(caminho_repo, token, repo=REPO_PADRAO, ref=BRANCH_PADRAO):
    """Retorna (conteudo_texto, sha) do arquivo no repo, ou (None, None) se não existir."""
    url = f"{API_BASE}/repos/{repo}/contents/{caminho_repo}"
    r = requests.get(url, headers=_headers(token), params={"ref": ref}, timeout=20)
    if r.status_code == 404:
        return None, None
    r.raise_for_status()
    dados = r.json()
    conteudo = base64.b64decode(dados["content"]).decode("utf-8")
    return conteudo, dados["sha"]


def _commit_bytes(caminho_repo, conteudo_bytes, sha, mensagem, token, repo, ref):
    url = f"{API_BASE}/repos/{repo}/contents/{caminho_repo}"
    payload = {
        "message": mensagem,
        "content": base64.b64encode(conteudo_bytes).decode("ascii"),
        "branch": ref,
    }
    if sha:
        payload["sha"] = sha
    return requests.put(url, headers=_headers(token), json=payload, timeout=20)


def _commit(caminho_repo, conteudo_texto, sha, mensagem, token, repo, ref):
    return _commit_bytes(caminho_repo, conteudo_texto.encode("utf-8"), sha, mensagem, token, repo, ref)


def obter_sha(caminho_repo, token, repo=REPO_PADRAO, ref=BRANCH_PADRAO):
    """Retorna o sha do arquivo no repo (para poder sobrescrever), ou None se ele
    ainda não existir. Diferente de baixar_arquivo(), não decodifica o conteúdo
    como texto — serve tanto para arquivo texto quanto binário (xlsx)."""
    url = f"{API_BASE}/repos/{repo}/contents/{caminho_repo}"
    r = requests.get(url, headers=_headers(token), params={"ref": ref}, timeout=20)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()["sha"]


def gravar_arquivo_binario(caminho_repo, conteudo_bytes, mensagem, token,
                            repo=REPO_PADRAO, ref=BRANCH_PADRAO, tentativas=3):
    """Cria ou sobrescreve um arquivo binário (ex: .xlsx) no repo via commit direto.
    Retorna (sucesso: bool, erro: str|None). Faz retry em caso de conflito de sha
    (commit concorrente), igual a gravar_linha_append()."""
    for tentativa in range(tentativas):
        try:
            sha = obter_sha(caminho_repo, token, repo=repo, ref=ref)
            resp = _commit_bytes(caminho_repo, conteudo_bytes, sha, mensagem, token, repo, ref)
            if resp.status_code in (200, 201):
                return True, None
            if resp.status_code == 409:
                time.sleep(1)
                continue
            return False, f"GitHub API respondeu {resp.status_code}: {resp.text[:300]}"
        except requests.RequestException as e:
            if tentativa == tentativas - 1:
                return False, str(e)
            time.sleep(1)
    return False, "Não foi possível gravar após múltiplas tentativas (conflito de commit)."


def gravar_linha_append(caminho_repo, colunas, nova_linha, mensagem, token,
                         repo=REPO_PADRAO, ref=BRANCH_PADRAO, tentativas=3):
    """
    Acrescenta uma linha a um CSV versionado no repo (cria o arquivo com cabeçalho se
    ainda não existir). Faz retry em caso de conflito de sha (commit concorrente).
    Retorna (sucesso: bool, erro: str|None).
    """
    for tentativa in range(tentativas):
        try:
            conteudo, sha = baixar_arquivo(caminho_repo, token, repo=repo, ref=ref)
            if conteudo is None:
                conteudo = None
            else:
                conteudo = _migrar_cabecalho(conteudo, colunas)

            saida = io.StringIO(conteudo or "")
            if conteudo is None:
                escritor = csv.writer(saida, lineterminator="\n")
                escritor.writerow(colunas)
            else:
                saida.seek(0, io.SEEK_END)
                if saida.getvalue() and not saida.getvalue().endswith("\n"):
                    saida.write("\n")
                escritor = csv.writer(saida, lineterminator="\n")
            escritor.writerow([str(nova_linha.get(c, "")) for c in colunas])
            novo_conteudo = saida.getvalue()

            resp = _commit(caminho_repo, novo_conteudo, sha, mensagem, token, repo, ref)
            if resp.status_code in (200, 201):
                return True, None
            if resp.status_code == 409:
                time.sleep(1)
                continue
            return False, f"GitHub API respondeu {resp.status_code}: {resp.text[:300]}"
        except requests.RequestException as e:
            if tentativa == tentativas - 1:
                return False, str(e)
            time.sleep(1)
    return False, "Não foi possível gravar após múltiplas tentativas (conflito de commit)."


def _migrar_cabecalho(conteudo, colunas):
    """
    Se o cabeçalho do CSV existente não bater com `colunas` (schema mudou desde o último
    commit — ex: nova coluna adicionada), reescreve o cabeçalho e preenche as linhas
    antigas com campo vazio nas colunas novas, para nunca ficar com linhas de tamanhos
    diferentes do cabeçalho (isso já quebrou a leitura do CSV uma vez em produção).
    """
    linhas = list(csv.reader(io.StringIO(conteudo)))
    if not linhas:
        return None
    if linhas[0] == list(colunas):
        return conteudo
    saida = io.StringIO()
    escritor = csv.writer(saida, lineterminator="\n")
    escritor.writerow(colunas)
    for linha in linhas[1:]:
        linha = (linha + [""] * len(colunas))[:len(colunas)]
        escritor.writerow(linha)
    return saida.getvalue()
