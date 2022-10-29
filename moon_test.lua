function remove_space(x)
    local b
    local y = ''
    for b=1, string.len(x), 1 do
        if string.sub(x,b,b) ~= ' ' then
            y = y .. string.sub(x,b,b)
        end
    end
    return y
end

function first_signal_add (x)
    local y = ''
    if string.sub(x,1,1) ~= '-' and string.sub(x,1,1) ~= '+' then
        y = y .. '+' .. x
    else
        y = x
    end
    return y
end

function to_array(x)

    local array = {}
    array["dice"] = {}
    array["signal"] = {}

    local stay = 0
    local current_dice = 1
    local current_signal = 1
    local s = 0

    local n1 = 0
    local n2 = 0


    while stay == 0 do

        if string.sub(x,1,1) == '-' or string.sub(x,1,1) == '+' then
            array["signal"][current_signal] = string.sub(x,1,1)
            current_signal = current_signal + 1
            x = x:sub(2);

        else

            n1 = string.find(x, '+')
            n2 = string.find(x, '-')

            if n1 ~= nil or n2 ~= nil then


                if n1 == nil then n1 = n2 + 1 end
                if n2 == nil then n2 = n1 + 1 end

                if n1 < n2 then
                    s = n1
                else
                    s = n2
                end
                array["dice"][current_dice] = string.sub(x, 1, s-1)
                current_dice = current_dice + 1
                x = x:sub(s);
            else
                array["dice"][current_dice] = x
                current_signal = 0
                current_dice = 0
                stay = 1
            end
        end
    end
    return array

end


function get_deep_roll(x)
    local resultado, rolagem = rolar(x);
    local dados = {};

    for i = 1, #rolagem.ops, 1 do
        local op = rolagem.ops[i];

        if op.tipo == "dado" then
            for j = 1, #op.resultados, 1 do
                dados[#dados + 1] = op.resultados[j];
            end;
        end;
    end;
    return dados
end


function rf(x)
    return string.sub(tostring(x),1,string.len(tostring(x))-2)
end

function roll_weird_dice(x)

    local i = 0
    local ii
    local c = 0
    local cc = 0

    for ii = 1, #x do
        i = i + 1;
    end

    local dv_find
    local dd_find

    local how_many
    local wich_dice

    local var = 0
    local var_cache = 0

    for c = 1, i, 1 do
        dv_find = string.find(x[c], 'dv')
        if dv_find ~= nil then
            if (dv_find==1) then
                how_many = 2
            else
                how_many = tonumber(string.sub(x[c], 1, dv_find-1))
            end
            if how_many > 10 then how_many=10 end
            if how_many == 1 then how_many=2 end
            wich_dice = x[c]:sub(dv_find+2)

            var = get_deep_roll(how_many .. "d" .. tostring(wich_dice))
            var_cache = 0
            for cc = 1, how_many, 1 do
                if var[cc] > var_cache then var_cache = var[cc] end
            end
            x[c] = rf(var_cache)
        end
        dd_find = string.find(x[c], 'dd')
        if dd_find ~= nil then
            if (dd_find==1) then
                how_many = 2
            else
                how_many = tonumber(string.sub(x[c], 1, dd_find-1))
            end
            if how_many > 10 then how_many=10 end
            if how_many == 1 then how_many=2 end
            wich_dice = x[c]:sub(dd_find+2)

            var = get_deep_roll(how_many .. "d" .. tostring(wich_dice))
            var_cache = 257
            for cc = 1, how_many, 1 do
                if var[cc] < var_cache then var_cache = var[cc] end
            end
            x[c] = rf(var_cache)
        end

    end
    return x
end

function to_roll(x)
    local i = 0
    local ii
    local c = 0
    local y = ""

    for ii = 1, #x['signal'] do
        i = i + 1;
    end
    for c = 1, i, 1 do
        y = y .. x["signal"][c] .. x["dice"][c]
    end
    return y
end

function verify_dumness(x)
    local s = ''
    local i = 0
    local ii = 0
    local xx
    local k = 0
    local c = 0
    -- removidos: [espaço], d, v, 1234567890
    local dum_chars = '!"#$%&' .. "'()*,./:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcefghijklmnopqrstuwxyz{|}~🌈"

    local smart_chars = {
        "d", "v", "+", "-", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"
    }

    local dum_x_equal = {
        '', 'd', 'dd', 'dv', 'v'
    }

    local dum_xx_equal = dum_x_equal

    local dum_x_unlike = {
        "d%+", "d%-", "v%+", "v%-", "vd", "\\", "%%", "%(", "%)", "%[", "%]", "ddd", "vv", "v ", "d ", "%+%+", "%+%-", "%-%+", "%-%-"
    }

    local dum_xx_unlike = {
        "ddd", "vv", "%+%+", "%+%-", "%-%+", "%-%-"
    }

    for c = 1, 5, 1 do
        if x == dum_x_equal[c] then return true end
    end

    xx = remove_space(x)
    for c = 1, 5, 1 do
        if xx == dum_xx_equal[c] then return true end
    end

    for c = 1, 19, 1 do
        if string.find(x,dum_x_unlike[c]) ~= nil then return true end
    end

    for c = 1, 6, 1 do
        if string.find(xx,dum_xx_unlike[c]) ~= nil then return true end
    end

    for i = 1, string.len(x), 1 do
        if string.find(dum_chars, string.sub(x, i, i)) ~= nil then return true end
    end

    if string.find(x,"ddv") ~= nil then return true end

    if string.find(x,"d") == nil then return true end

    if tonumber(xx:sub(-1)) == nil then return true end

    for i = 1, string.len(xx), 1 do
        k = 0
        ii=1
        while k == 0 do
            if string.sub(xx, i, i) == smart_chars[ii] then k = 1 end
            if ii == 14 and k == 0 then k = 2 end
            ii = ii + 1
        end
        if k == 0 or k == 2 then return true end
    end

    return false
end


local inpt = parametro;
if parametro ~= '' then
    if verify_dumness(parametro) == false then
        local inpt_array;

        enviar('Rolando: ' .. parametro)

        inpt = remove_space(inpt)

        inpt = first_signal_add(inpt)

        inpt_array = to_array(inpt)

        inpt_array['dice'] = roll_weird_dice(inpt_array['dice'])

        inpt = to_roll(inpt_array)

        if string.find(inpt, 'd') ~=nil then

            return rolar(inpt:sub(2))
        else
            inpt = '0' .. inpt
            inpt = string.gsub(inpt, '+', ' + ')
            inpt = string.gsub(inpt, '-', ' - ')
            enviar('Resultado: ' .. inpt:sub(5) .. ' = '.. tostring(assert(load('return ' .. inpt))()))
        end
    else
        enviar(' sou idiota, escrevi errado! (caractere não suportado/escreveu errado/retardado)')
    end
else
    enviar('tenta dnv...(parametros vazios)')
end