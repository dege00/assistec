#!/usr/bin/env bash
#
# Backup do Assistec: dump comprimido do PostgreSQL + tar.gz do volume de mídia.
# Deve rodar na raiz do projeto (onde está o docker-compose.yml).
#
# Uso:
#   ./scripts/backup.sh
#
# Variáveis (opcionais):
#   DIRETORIO_BACKUP      destino local           (padrão: /var/backups/assistec)
#   DIAS_RETENCAO         dias de retenção        (padrão: 14)
#   COMPOSE_PROJECT_NAME  nome do projeto compose (padrão: assistec)
#   POSTGRES_USER         usuário do banco        (padrão: assistec)
#   POSTGRES_DB           nome do banco           (padrão: assistec)
#   VOLUME_MEDIA          volume da mídia         (padrão: ${COMPOSE_PROJECT_NAME}_media)
#   IMAGEM_HELPER         imagem para o tar       (padrão: alpine:3)
set -euo pipefail

DIRETORIO_BACKUP="${DIRETORIO_BACKUP:-/var/backups/assistec}"
DIAS_RETENCAO="${DIAS_RETENCAO:-14}"
PROJETO="${COMPOSE_PROJECT_NAME:-assistec}"
POSTGRES_USER="${POSTGRES_USER:-assistec}"
POSTGRES_DB="${POSTGRES_DB:-assistec}"
VOLUME_MEDIA="${VOLUME_MEDIA:-${PROJETO}_media}"
IMAGEM_HELPER="${IMAGEM_HELPER:-alpine:3}"

cd "$(dirname "$0")/.."

DATA="$(date +%F-%H%M)"
BANCO="$DIRETORIO_BACKUP/banco-$DATA.sql.gz"
MEDIA="$DIRETORIO_BACKUP/media-$DATA.tar.gz"

mkdir -p "$DIRETORIO_BACKUP"

echo "[backup] $(date -Is) dump do banco -> $BANCO"
docker compose exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$BANCO"
gzip -t "$BANCO"  # falha se o dump saiu corrompido/incompleto

echo "[backup] $(date -Is) mídia (volume $VOLUME_MEDIA) -> $MEDIA"
docker run --rm \
  -v "${VOLUME_MEDIA}:/media:ro" \
  -v "${DIRETORIO_BACKUP}:/backup" \
  "$IMAGEM_HELPER" \
  tar czf "/backup/media-$DATA.tar.gz" -C /media .
tar tzf "$MEDIA" >/dev/null  # valida o arquivo gerado

echo "[backup] $(date -Is) removendo arquivos com mais de $DIAS_RETENCAO dias"
find "$DIRETORIO_BACKUP" -type f \( -name 'banco-*.sql.gz' -o -name 'media-*.tar.gz' \) -mtime +"$DIAS_RETENCAO" -delete

echo "[backup] $(date -Is) concluído"
ls -lh "$BANCO" "$MEDIA"
