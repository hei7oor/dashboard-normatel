# 🚀 Como Publicar o Dashboard (passo a passo)

Resultado final: um **link** (ex: `https://normatel-dashboard.streamlit.app`) que
qualquer gerente abre no navegador ou celular, sem instalar nada.

Tudo é **gratuito**.

---

## ETAPA 1 — Criar conta no GitHub (onde o código fica guardado)

1. Acesse **https://github.com/signup**
2. Crie a conta com seu e-mail (heitorfernandesmaciel@gmail.com)
3. Confirme o e-mail

> Já tem conta? Pule para a Etapa 2.

---

## ETAPA 2 — Criar o repositório (a "pasta na nuvem")

1. Acesse **https://github.com/new**
2. **Repository name:** `dashboard-normatel`
3. Marque **Private** (🔒 dados da empresa ficam protegidos — recomendado)
4. **NÃO** marque "Add a README"
5. Clique em **Create repository**
6. Deixe essa página aberta — vamos usar o endereço dela.

---

## ETAPA 3 — Enviar o código para o GitHub

Abra o **Git Bash** (ou o terminal) **nesta pasta do projeto** e cole os
comandos abaixo, **trocando `SEU-USUARIO`** pelo seu nome de usuário do GitHub:

```bash
git remote add origin https://github.com/SEU-USUARIO/dashboard-normatel.git
git push -u origin master
```

> Vai abrir uma janela pedindo login do GitHub — faça o login no navegador.
> (Se pedir senha no terminal, use um "Personal Access Token" — me avise que te explico.)

---

## ETAPA 4 — Publicar no Streamlit (transforma em site)

1. Acesse **https://share.streamlit.io**
2. Clique em **Sign in with GitHub** e autorize
3. Clique em **Create app** → **Deploy a public app from GitHub**
4. Preencha:
   - **Repository:** `SEU-USUARIO/dashboard-normatel`
   - **Branch:** `master`
   - **Main file path:** `app_beta.py`   ← (importante: é a versão nova)
   - **App URL:** escolha algo como `normatel-dashboard`
5. Clique em **Deploy!**

Aguarde 1–3 minutos. Pronto: seu dashboard estará no ar! 🎉

---

## ETAPA 5 — Compartilhar com a gerência

- Copie o link gerado (ex: `https://normatel-dashboard.streamlit.app`)
- Envie por e-mail / WhatsApp / Teams

### Quer restringir quem vê? (dados sensíveis)
No painel do Streamlit: **Settings → Sharing** → adicione os e-mails dos
gerentes. Só quem estiver na lista (e logar com Google) consegue abrir.

---

## ATUALIZAR OS DADOS depois de publicado

Quando tiver planilhas novas:
1. Substitua os arquivos na pasta `dados/`
2. No terminal, rode:
   ```bash
   git add -A
   git commit -m "atualiza dados"
   git push
   ```
3. O site atualiza sozinho em ~1 minuto.

---

## ⚠️ Importante
- O arquivo `.streamlit/secrets.toml` (sua chave) **não vai** para o GitHub
  (está protegido). A IA funciona sem ele, com respostas dos dados.
- A versão original (`app.py`) continua salva como backup (tag `v1.0`).
