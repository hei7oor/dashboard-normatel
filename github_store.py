"""
Persiste dados no próprio repositório do GitHub via commit (API REST de Contents),
sem precisar de `git` instalado nem de banco de dados externo. Usado para o CSV de
respostas manuais e para o histórico diário de KPIs.
"""
import base64
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


def _commit(caminho_repo, conteudo_texto, sha, mensagem, token, repo, ref):
    url = f"{API_BASE}/repos/{repo}/contents/{caminho_repo}"
    payload = {
        "message": mensagem,
        "content": base64.b64encode(conteudo_texto.encode("utf-8")).decode("ascii"),
        "branch": ref,
    }
    if sha:
        payload["sha"] = sha
    return requests.put(url, headers=_headers(token), json=payload, timeout=20)


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
                cabecalho = ",".join(colunas)
                conteudo = cabecalho + "\n"
            linha_csv = ",".join(_csv_escapar(str(nova_linha.get(c, ""))) for c in colunas)
            novo_conteudo = conteudo
            if not novo_conteudo.endswith("\n"):
                novo_conteudo += "\n"
            novo_conteudo += linha_csv + "\n"

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


def _csv_escapar(valor):
    if any(c in valor for c in [",", '"', "\n"]):
        return '"' + valor.replace('"', '""') + '"'
    return valor
