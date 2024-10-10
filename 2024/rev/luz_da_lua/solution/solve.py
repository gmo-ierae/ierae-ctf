# https://sourceforge.net/projects/unluac/
# $ java -jar unluac_2023_12_24.jar ./LuzDaLua.luac                                                                                    [/home/k/ctf/ieraectf/03_LuzDaLua]
# io.write("Input > ")
# input = io.read("*l")
# if 28 ~= string.len(input) then
# elseif string.byte(input, 1) ~ 232 ~= 161 then
# elseif 43 ~= string.byte(input, 2) ~ 110 then
# elseif string.byte(input, 3) ~ 178 ~= 224 then
# elseif string.byte(input, 4) ~ 172 ~= 237 then
# elseif string.byte(input, 5) ~ 212 ~= 145 then
# elseif 98 ~= string.byte(input, 6) ~ 25 then
# elseif 121 ~= string.byte(input, 7) ~ 53 then
# elseif 74 ~= string.byte(input, 8) ~ 63 then
# elseif string.byte(input, 9) ~ 135 ~= 230 then
# elseif 3 ~= string.byte(input, 10) ~ 92 then
# elseif 23 ~= string.byte(input, 11) ~ 38 then
# elseif string.byte(input, 12) ~ 250 ~= 137 then
# elseif 135 ~= string.byte(input, 13) ~ 216 then
# elseif 86 ~= string.byte(input, 14) ~ 5 then
# elseif 117 ~= string.byte(input, 15) ~ 69 then
# elseif string.byte(input, 16) ~ 226 ~= 189 then
# elseif string.byte(input, 17) ~ 137 ~= 186 then
# elseif string.byte(input, 18) ~ 148 ~= 240 then
# elseif 53 ~= string.byte(input, 19) ~ 64 then
# elseif string.byte(input, 20) ~ 130 ~= 225 then
# elseif string.byte(input, 21) ~ 241 ~= 197 then
# elseif string.byte(input, 22) ~ 151 ~= 227 then
# elseif 250 ~= string.byte(input, 23) ~ 203 then
# elseif string.byte(input, 24) ~ 179 ~= 220 then
# elseif string.byte(input, 25) ~ 216 ~= 182 then
# elseif 4 ~= string.byte(input, 26) ~ 101 then
# elseif 130 ~= string.byte(input, 27) ~ 238 then
# elseif 64 ~= string.byte(input, 28) ~ 61 then
# else
#   print("Correct")
#   goto lbl_305
# end
# print("Wrong")
# ::lbl_305::

flag = ''
flag += chr(232 ^ 161)
flag += chr(43 ^ 110)
flag += chr(178 ^ 224)
flag += chr(172 ^ 237)
flag += chr(212 ^ 145)
flag += chr(98 ^ 25)
flag += chr(121 ^ 53)
flag += chr(74 ^ 63)
flag += chr(135 ^ 230)
flag += chr(3 ^ 92)
flag += chr(23 ^ 38)
flag += chr(250 ^ 137)
flag += chr(135 ^ 216)
flag += chr(86 ^ 5)
flag += chr(117 ^ 69)
flag += chr(226 ^ 189)
flag += chr(137 ^ 186)
flag += chr(148 ^ 240)
flag += chr(53 ^ 64)
flag += chr(130 ^ 225)
flag += chr(241 ^ 197)
flag += chr(151 ^ 227)
flag += chr(250 ^ 203)
flag += chr(179 ^ 220)
flag += chr(216 ^ 182)
flag += chr(4 ^ 101)
flag += chr(130 ^ 238)
flag += chr(64 ^ 61)

print(flag)

