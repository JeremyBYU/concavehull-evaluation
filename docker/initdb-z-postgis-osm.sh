export PGUSER="$POSTGRES_USER"
createuser --no-superuser --no-createrole --createdb concave
createdb -E UTF8 -O concave concave
psql -d concave -c "CREATE EXTENSION postgis;"
psql -d concave -c "CREATE EXTENSION hstore;" # only required for hstore support
echo "ALTER USER concave WITH PASSWORD 'concave';" |psql -d concave