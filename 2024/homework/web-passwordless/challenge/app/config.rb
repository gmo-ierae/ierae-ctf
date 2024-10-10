require 'sequel'
require 'securerandom'

# DB config
DB = Sequel.mysql2(
  host: ENV['MYSQL_HOST'] || 'mysql',
  user: ENV['MYSQL_USER'],
  password: ENV['MYSQL_PASSWORD'] || '',
  database: ENV['MYSQL_DATABASE'],
)

DB.create_table? :users do
  primary_key :id
  String :name, null: false, unique: true
  String :email, null: false, unique: true
  String :profile, null: false
end

DB.create_table? :login_tokens do
  primary_key :id
  foreign_key :user_id, :users
  String :key, null: false, unique: true
  String :secret, null: false
end

class User < Sequel::Model
end

class LoginToken < Sequel::Model
end

# Create Admin user
if User.find(name: 'admin').nil?
  User.create(
    name: 'admin',
    email: 'admin@localhost',
    profile: ENV["FLAG"]
  )
end
