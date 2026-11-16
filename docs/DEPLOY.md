# Deploy do Assistec em uma VPS (Ubuntu LTS)

Passo a passo do zero até o sistema no ar, com backup e monitoramento. Troque
`SEU_DOMINIO`, `SEU_IP` e `SEU_EMAIL` pelos valores reais. Nenhum segredo deve
ir para o Git.

## 0. Requisitos

- Uma VPS com **Ubuntu 22.04 LTS** ou **24.04 LTS** e acesso root inicial.
- Um domínio (ou subdomínio) que você possa apontar para o IP da VPS.
- Uma conta em um serviço de backup fora da VPS (sugestão: **Backblaze B2**).
- Uma conta no **UptimeRobot** (ou similar) para monitorar a saúde.

## 1. Usuário não-root e acesso só por chave SSH

No primeiro acesso (como `root`):

```bash
adduser deploy                      # defina uma senha forte quando pedir
usermod -aG sudo deploy
```

No **seu computador**, copie sua chave pública para o servidor:

```bash
ssh-copy-id deploy@SEU_IP
```

Confirme que entra sem senha (`ssh deploy@SEU_IP`) e então **desabilite senha e
login de root** no servidor:

```bash
sudo nano /etc/ssh/sshd_config
```

Ajuste (ou descomente) estas linhas:

```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
```

Recarregue o SSH e teste em outra janela antes de fechar a atual:

```bash
sudo systemctl reload ssh
```

## 2. Firewall (ufw)

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP (redireciona/valida o certificado)
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
sudo ufw status
```

## 3. Atualizações automáticas de segurança

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades   # responda "Yes"
```

## 4. Docker e Docker Compose

```bash
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker deploy     # saia e entre de novo para valer
```

## 5. DNS

No painel do seu provedor de domínio, crie um registro **A** apontando
`SEU_DOMINIO` para `SEU_IP`. Aguarde a propagação (confira com `dig SEU_DOMINIO +short`).

O Caddy só consegue emitir o certificado HTTPS quando o DNS já aponta para a VPS.

## 6. Código e `.env`

```bash
sudo mkdir -p /opt/assistec && sudo chown deploy:deploy /opt/assistec
git clone <URL_DO_REPOSITORIO> /opt/assistec
cd /opt/assistec
cp .env.example .env
```

Gere uma `SECRET_KEY` forte e edite o `.env`:

```bash
openssl rand -base64 48      # cole em SECRET_KEY
nano .env
```

`.env` esperado (sem valores reais aqui):

```
SECRET_KEY=<cole a chave gerada, 32+ caracteres>
DEBUG=0
DOMINIO=SEU_DOMINIO
ALLOWED_HOSTS=SEU_DOMINIO
CSRF_TRUSTED_ORIGINS=https://SEU_DOMINIO
FRONTEND_URL=https://SEU_DOMINIO
POSTGRES_PASSWORD=<senha forte do banco>
```

Proteja o arquivo: `chmod 600 .env`.

## 7. Subir a aplicação

```bash
cd /opt/assistec
docker compose up -d --build
docker compose ps
```

Abra `https://SEU_DOMINIO` (o Caddy emite o certificado automaticamente).

## 8. Criar a loja do cliente

```bash
docker compose exec backend python manage.py criar_loja \
  --nome-loja "Nome da Assistência" \
  --usuario cliente --nome "Nome da Pessoa" --telefone "86 99999-0000"
```

Se `--senha` não for informada, o comando gera uma senha forte e a mostra **uma
única vez** — anote e entregue ao cliente. Para redefinir depois:

```bash
docker compose exec backend python manage.py resetar_senha --usuario cliente
```

## 9. Backup

### 9.1 Rodar uma vez à mão

```bash
cd /opt/assistec
sudo mkdir -p /var/backups/assistec
sudo chown deploy:deploy /var/backups/assistec
chmod +x scripts/*.sh
./scripts/backup.sh
ls -lh /var/backups/assistec
```

O script faz `pg_dump` comprimido do banco e um `tar.gz` do volume de mídia,
com data no nome, e apaga o que tiver mais de 14 dias. Se qualquer etapa falhar,
ele termina com erro (e o cron registra a falha).

### 9.2 Enviar para fora da VPS (rclone)

Instale o rclone e crie a configuração do remoto:

```bash
sudo apt install -y rclone
sudo mkdir -p /etc/rclone
sudo rclone config --config /etc/rclone/rclone.conf
```

No assistente, escolha **New remote** → nome `b2` → provedor **Backblaze B2** e
informe o `keyID` e o `applicationKey` da sua conta. O arquivo
`/etc/rclone/rclone.conf` fica com o formato:

```
[b2]
type = b2
account = <keyID>
key = <applicationKey>
```

Proteja o arquivo (`sudo chmod 600 /etc/rclone/rclone.conf`) e teste:

```bash
RCLONE_DESTINO="b2:meu-bucket/assistec" ./scripts/enviar_backup.sh
```

### 9.3 Agendar no cron

```bash
crontab -e
```

Adicione (backup diário às 03:00 e envio logo depois; falha vira linha no log):

```cron
# Backup diário às 03:00; registra falha em /var/log/assistec-backup.log
0 3 * * * cd /opt/assistec && ./scripts/backup.sh >> /var/log/assistec-backup.log 2>&1 && RCLONE_DESTINO="b2:meu-bucket/assistec" ./scripts/enviar_backup.sh >> /var/log/assistec-backup.log 2>&1 || echo "$(date -Is) FALHA no backup" >> /var/log/assistec-backup.log

# A cada 5 minutos checa a saúde e registra se estiver fora do ar
*/5 * * * * curl -fsS https://SEU_DOMINIO/api/saude/ >/dev/null || echo "$(date -Is) saude: fora do ar" >> /var/log/assistec-saude.log
```

Garanta que `deploy` possa escrever nos logs:

```bash
sudo touch /var/log/assistec-backup.log /var/log/assistec-saude.log
sudo chown deploy:deploy /var/log/assistec-*.log
```

## 10. Monitoramento (UptimeRobot)

Crie um monitor do tipo **HTTP(s)** apontando para
`https://SEU_DOMINIO/api/saude/`. O endpoint é público, faz um `SELECT 1` no
banco e responde `{"status": "ok"}` (HTTP 200); se o banco cair, responde 503.
Nenhum dado é exposto. Configure o alerta por e-mail/Telegram.

## 11. Testar a restauração ANTES de colocar cliente real

Nunca confie em um backup que você não restaurou. Rode o `backup.sh`, depois
restaure em um banco e volume de **teste** (não toca em produção):

```bash
cd /opt/assistec
./scripts/backup.sh
./scripts/restaurar.sh /var/backups/assistec/banco-*.sql.gz /var/backups/assistec/media-*.tar.gz
```

O script imprime as contagens (lojas, clientes, peças, ordens, fotos) do banco
restaurado — compare com a produção. Só depois de a restauração bater é que o
sistema está pronto para dados reais.

Para sobrescrever **produção** de propósito (recuperação de desastre), use
`--producao` e digite `CONFIRMAR` quando pedido:

```bash
./scripts/restaurar.sh --producao /var/backups/assistec/banco-....sql.gz /var/backups/assistec/media-....tar.gz
```

## 12. Atualizar o sistema

```bash
cd /opt/assistec
git pull
docker compose up -d --build
docker compose exec backend python manage.py migrate --noinput
```

## 13. Operação do dia a dia

```bash
docker compose ps                       # estado dos containers
docker compose logs -f backend          # logs da API
docker compose exec db psql -U assistec assistec   # abrir o banco
docker compose restart backend          # reiniciar a API
```

Os logs dos containers são limitados a 10 MB por arquivo, com no máximo 3
arquivos, para não encher o disco da VPS.
