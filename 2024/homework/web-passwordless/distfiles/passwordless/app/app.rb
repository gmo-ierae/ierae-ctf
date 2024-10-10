require 'sinatra'
require 'json'
require 'ipaddr'

require './config'

# SQL文を確認したい時用
# require 'logger'
# DB.sql_log_level = :debug
# DB.loggers << Logger.new($stderr)

# ログイントークンをユーザのメールアドレスに送信する
def send_login_token(user, login_token)
  # TODO: 来年実装する
end

# Unprintableな文字が飛んできたらハッカーなので止める
before do
  params.each do |k, v|
    if /[^[:print:]]/.match?(v.to_s)
      halt 400, "Hacker detected!"
    end
  end
end

get '/' do
  send_file File.join(settings.public_folder, 'index.html')
end

post '/login' do
  content_type :json

  # adminは通常のログインフォームからはログインできない
  if params[:name].match?(/admin/i)
    return { error: 'You can\'t login as admin' }.to_json
  end

  user = User.find(name: params[:name])
  return { error: 'Not found' }.to_json if user.nil?

  # 重複しないようにIPアドレスをつけておく
  secret = IPAddr.new(request.ip).to_i.to_s + SecureRandom.hex(32)
  login_token = LoginToken.create(
    user_id: user.id,
    key: SecureRandom.hex(32),
    secret: secret
  )
  send_login_token(user, login_token)

  {
    login_token_key: login_token.key
  }.to_json
end

post '/login/:key' do
  content_type :json

  login_token = LoginToken.find(key: params[:key], secret: params[:secret])
  return { error: 'Not found' }.to_json if login_token.nil?

  user = User.find(id: login_token.user_id)

  {
    user: {
      id: user.id,
      name: user.name,
      email: user.email,
      profile: user.profile
    }
  }.to_json
end

post "/register" do
  content_type :json

  user = User.create(
    name: params[:name],
    email: params[:email],
    profile: params[:profile]
  )

  {
    user: {
      id: user.id,
      name: user.name,
      email: user.email,
      profile: user.profile
    }
  }.to_json
end
