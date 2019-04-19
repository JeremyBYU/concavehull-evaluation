SELECT DropGeoTable('concave');

CREATE TABLE concave (
id INTEGER NOT NULL PRIMARY KEY,
test_name TEXT);

SELECT AddGeometryColumn('concave', 'Geometry', -1, 'Point', 'XY');