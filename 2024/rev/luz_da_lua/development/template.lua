io.write('Input > ')
input = io.read("*l")

if string.len(input) ~= FLAG_LEN then
    goto wrong
end

VALIDATE_FLAG

print('Correct')
goto exit

::wrong::
print('Wrong')

::exit::
