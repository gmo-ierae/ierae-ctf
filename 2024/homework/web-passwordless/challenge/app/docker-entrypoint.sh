#!/bin/bash

mysqld --user=$MYSQL_USER &

# Wait mysql server wakes up
while ! mysqladmin ping -h $MYSQL_HOST -u $MYSQL_USER; do
  sleep 1;
done

echo "CREATE DATABASE IF NOT EXISTS \`$MYSQL_DATABASE\` ;" | mysql -u $MYSQL_USER

bundle exec ruby app.rb
