io.write('Input > ')
input = io.read("*l")

if string.len(input) ~= 28 then
    goto wrong
end

if string.byte(input, 1) ~ 232 ~= 161 then goto wrong end
if string.byte(input, 2) ~ 110 ~= 43 then goto wrong end
if string.byte(input, 3) ~ 178 ~= 224 then goto wrong end
if string.byte(input, 4) ~ 172 ~= 237 then goto wrong end
if string.byte(input, 5) ~ 212 ~= 145 then goto wrong end
if string.byte(input, 6) ~ 25 ~= 98 then goto wrong end
if string.byte(input, 7) ~ 53 ~= 121 then goto wrong end
if string.byte(input, 8) ~ 63 ~= 74 then goto wrong end
if string.byte(input, 9) ~ 135 ~= 230 then goto wrong end
if string.byte(input, 10) ~ 92 ~= 3 then goto wrong end
if string.byte(input, 11) ~ 38 ~= 23 then goto wrong end
if string.byte(input, 12) ~ 250 ~= 137 then goto wrong end
if string.byte(input, 13) ~ 216 ~= 135 then goto wrong end
if string.byte(input, 14) ~ 5 ~= 86 then goto wrong end
if string.byte(input, 15) ~ 69 ~= 117 then goto wrong end
if string.byte(input, 16) ~ 226 ~= 189 then goto wrong end
if string.byte(input, 17) ~ 137 ~= 186 then goto wrong end
if string.byte(input, 18) ~ 148 ~= 240 then goto wrong end
if string.byte(input, 19) ~ 64 ~= 53 then goto wrong end
if string.byte(input, 20) ~ 130 ~= 225 then goto wrong end
if string.byte(input, 21) ~ 241 ~= 197 then goto wrong end
if string.byte(input, 22) ~ 151 ~= 227 then goto wrong end
if string.byte(input, 23) ~ 203 ~= 250 then goto wrong end
if string.byte(input, 24) ~ 179 ~= 220 then goto wrong end
if string.byte(input, 25) ~ 216 ~= 182 then goto wrong end
if string.byte(input, 26) ~ 101 ~= 4 then goto wrong end
if string.byte(input, 27) ~ 238 ~= 130 then goto wrong end
if string.byte(input, 28) ~ 61 ~= 64 then goto wrong end


print('Correct')
goto exit

::wrong::
print('Wrong')

::exit::
