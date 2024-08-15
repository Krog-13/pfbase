#!/bin/bash

# dump the database
docker exec local_pgdb pg_dump -U kmg_user -d report > /local_path/dump_`date +%d-%m-%Y%H_%M_%S`.sql



# copy file in container pg
# docker cp /local_path/dump_04-08-2023.sql local_pgdb:/tmp/dump_file.sql

# restore the database
# docker exec -it local_pgdb psql -U kmg_user -d report -f /tmp/dump_file.sql



# attention rename local_path
# username and dbname should be the same
