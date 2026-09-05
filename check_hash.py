import bcrypt

h1 = '$2b$12$yueHjUP8w0PEtdUJjcfNcuiKmetz9uMmnepm9otuCDkAssxQIDN7W'
h2 = '$2b$12$lm8i3FUY51m4ijts7wrb6.Kar/6cVv4dAW6XWOqmf/arIV2b7/WmO'

print('hash1(schema) vs admin123456:', bcrypt.checkpw(b'admin123456', h1.encode()))
print('hash2(seed)   vs admin123456:', bcrypt.checkpw(b'admin123456', h2.encode()))
