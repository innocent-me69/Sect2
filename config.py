env_vars = {
  # Get From my.telegram.org
  "API_HASH": "e9bfc473049cbaeff901ca6892d559c7",
  # Get From my.telegram.org
  "API_ID": "20373005",
  #Get For @BotFather
  "BOT_TOKEN": "7832627909:AAFRe0I_9hrbJOlbbkZNHFhp5unHh4_mUh8",
  # Get For tembo.io
  "DATABASE_URL_PRIMARY": "postgresql://postgres:C4VEgkZOIsrV0to9@rustically-undaunted-mastodon.data-1.use1.tembo.io:5432/postgres",
  # Logs Channel Username Without @
  "CACHE_CHANNEL": "dump_manhwa",
  # Force Subs Channel username without @
  "CHANNEL": "Manga_Sect",
  # {chap_num}: Chapter Number
  # {chap_name} : Manga Name
  # Ex : Chapter {chap_num} {chap_name} @Manhwa_Arena
  "FNAME": "[MS] [{chap_num}] {chap_name} @Manga_Sect"  

}
dbname = env_vars.get('DATABASE_URL_PRIMARY') or env_vars.get('DATABASE_URL') or 'sqlite:///test.db'

if dbname.startswith('postgres://'):
    dbname = dbname.replace('postgres://', 'postgresql://', 1)
    
