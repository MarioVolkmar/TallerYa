# uso: fotos.sh <carpeta> <url_galgo> <regex_nombre> [max]
d="/c/dev/TallerYa/manual_despiece/$1/fotos"; mkdir -p "$d"
n=0
for img in $(curl -sL -A "Mozilla/5.0" "$2" | grep -oE 'https://images\.ctfassets\.net/[^"'"'"' )]+\.(jpg|jpeg|png|webp)' | sort -u | grep -iE "$3" | head -${4:-5}); do
  n=$((n+1)); f="$d/galgo_$n.jpg"
  curl -sL -A "Mozilla/5.0" -o "$f" "$img?w=900&fm=jpg&q=80"
  t=$(file -b --mime-type "$f"); [ "$t" = "image/jpeg" ] || { rm -f "$f"; echo "descartado $img ($t)"; continue; }
  echo "galgo_$n.jpg  $img  (pagina: $2)" >> "$d/fuentes.txt"; echo "ok $f"
done
