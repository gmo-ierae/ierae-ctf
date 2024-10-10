use std::io::{self, Write};
use std::arch::asm;

const KEY_SIZE: usize = 32;
const STATE_NUM: usize = 8;
const MSG_BLOCK_SIZE: usize = 32;

#[derive(Default, Clone)]
struct CipherContext {
    key: [u128; KEY_SIZE / 16],
    state: [u128; STATE_NUM],
    size_ad: usize,
    size_m: usize,
}

#[derive(Debug)]
struct BackdoorError {
    msg: u64,
    data: Vec<u8>,
}

// FIPS 180-2, 4.2.3 SHA-384 and SHA-512 Constants
const Z0: u128 = 0x4cc5d4becb3e42b6597f299cfc657e2a;
const Z1: u128 = 0x5fcb6fab3ad6faec6c44198c4a475817;

const INIT_LOOP: usize = 20;

fn convert_u128_to_u8(input: Vec<u128>) -> Vec<u8> {
    input.iter()
         .flat_map(|value| value.to_le_bytes().to_vec())
         .collect()
}

fn convert_u8_to_u128(u8_vec: Vec<u8>) -> Result<Vec<u128>, &'static str> {
    if u8_vec.len() % 16 != 0 {
        if cfg!(debug_assertions) {
            return Err("The length of u8 vector is not a multiple of 16.");
        } else {
            return Err("");
        }
    }

    let mut u128_vec = Vec::new();
    for chunk in u8_vec.chunks_exact(16) {
        let array: [u8; 16] = chunk.try_into().unwrap();
        u128_vec.push(u128::from_le_bytes(array));
    }

    Ok(u128_vec)
}

fn u128_to_vec_u8(value: u128) -> Vec<u8> {
    value.to_le_bytes().to_vec()
}

fn vec_u8_to_u128(vec: &[u8]) -> u128 {
    let mut array = [0u8; 16];
    array.copy_from_slice(vec);
    u128::from_le_bytes(array)
}

fn enc(val: u128, rkey: u128) -> u128 {
    let val_vec = u128_to_vec_u8(val);
    let rkey_vec = u128_to_vec_u8(rkey);
    let mut result_vec = vec![0u8; 16];

    unsafe {
        asm!(
            "movdqu xmm0, [{val}]",
            "movdqu xmm1, [{rkey}]",
            "aesenc xmm0, xmm1",
            "movdqu [{result}], xmm0",
            val = in(reg) val_vec.as_ptr(),
            rkey = in(reg) rkey_vec.as_ptr(),
            result = in(reg) result_vec.as_mut_ptr(),
            options(nostack, readonly)
        );
    }

    vec_u8_to_u128(&result_vec)
}

fn initialize_context(ctx: &mut CipherContext, key: [u128; KEY_SIZE / 16], iv: [u128; 1]) {
    let mut state = [0u128; STATE_NUM];
    let mut state_new = [0u128; STATE_NUM];
    let mut c = [0u128; 2];

    state[0] = key[1];
    state[1] = iv[0];
    state[2] = Z0;
    state[3] = Z1;
    state[4] = state[1] ^ state[0];
    state[5] = 0;
    state[6] = key[0];
    state[7] = 0;
    c[0] = state[2];
    c[1] = state[3];

    for _ in 0..INIT_LOOP {
        state_new[0] = state[7] ^ c[0];
        state_new[1] = enc(state[0], state[7]);
        state_new[2] = state[1] ^ state[6];
        state_new[3] = enc(state[2], state[1]);
        state_new[4] = state[3] ^ c[1];
        state_new[5] = enc(state[4], state[3]);
        state_new[6] = enc(state[5], state[4]);
        state_new[7] = state[6] ^ state[0];
        state.clone_from_slice(&state_new);
    }
    state[0] ^= key[0];
    state[4] ^= key[1];

    ctx.state.copy_from_slice(&state);
    ctx.key.copy_from_slice(&key);
    ctx.size_ad = 0;
    ctx.size_m = 0;
}

fn encrypt_data(ctx: &mut CipherContext, data: &[u8]) -> Result<Vec<u8>, &'static str> {
    let mut state: [u128; 8] = ctx.state.clone();
    let mut state_new: [u128; 8] = [0u128; STATE_NUM];
    let mut m: [u128; 2] = [0u128; 2];
    let mut z: [u128; 2] = [0u128; 2];
    let mut c: [u128; 2] = [0u128; 2];

    let in_pad_len = if data.len() % MSG_BLOCK_SIZE == 0 {
        data.len()
    } else {
        (data.len() / MSG_BLOCK_SIZE + 1) * MSG_BLOCK_SIZE
    };
    let mut in_padded = vec![0u8; in_pad_len];
    in_padded[..data.len()].copy_from_slice(&data);

    let in_u128 = convert_u8_to_u128(in_padded)?;
    let mut out_u128 = vec![0u128; in_u128.len()];

    for (i, chunk) in in_u128.chunks(2).enumerate() {
        m[0] = chunk[0];
        m[1] = chunk[1];

        z[0] = enc(state[1], state[5]);
        z[1] = enc(state[0] ^ state[4], state[2]);

        c[0] = m[0] ^ z[0];
        c[1] = m[1] ^ z[1];

        out_u128[2 * i] = c[0];
        out_u128[2 * i + 1] = c[1];

        state_new[0] = state[7] ^ c[0];
        state_new[1] = enc(state[0], state[7]);
        state_new[2] = state[1] ^ state[6];
        state_new[3] = enc(state[2], state[1]);
        state_new[4] = state[3] ^ c[1];
        state_new[5] = enc(state[4], state[3]);
        state_new[6] = enc(state[5], state[4]);
        state_new[7] = state[6] ^ state[0];

        state.clone_from_slice(&state_new);
    }

    ctx.state.clone_from_slice(&state);
    ctx.size_m += data.len();

    let encrypted = convert_u128_to_u8(out_u128);
    Ok(encrypted)
}


fn print_menu() {
    println!("1. Encrypt");
    println!("2. Get Encrypted Flag");
    println!("3. Exit");
    print!("> ");
    io::stdout().flush().unwrap();
}

fn b64decode(input: &str) -> Result<Vec<u8>, BackdoorError> {
    let mut output = Vec::new();
    let mut buffer = 0;
    let mut buffer_count = 0;

    for c in input.chars() {
        let value = match c {
            'A'..='Z' => c as u8 - b'A',
            'a'..='z' => c as u8 - b'a' + 26,
            '0'..='9' => c as u8 - b'0' + 52,
            '+' => 62,
            '/' => 63,
            '=' => break,
            _ => return Err(BackdoorError {
                msg: 0,
                data: output,
            }),
        };
        buffer = (buffer << 6) | value as u64;
        buffer_count += 6;
        if buffer_count >= 8 {
            output.push((buffer >> (buffer_count - 8)) as u8);
            buffer_count -= 8;
        }
    }

    if buffer_count == 4 && buffer & 0b1000 != 0 {
        return Err(BackdoorError {
            msg: buffer,
            data: output,
        });
    }

    Ok(output)
}

const BASE64_TABLE: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

fn b64encode(data: Vec<u8>) -> String {
    let mut encoded = String::new();

    for chunk in data.chunks(3) {
        let mut buffer = [0u8; 3];
        buffer[..chunk.len()].copy_from_slice(chunk);

        let b1 = buffer[0] >> 2;
        let b2 = ((buffer[0] & 0b00000011) << 4) | (buffer[1] >> 4);
        let b3 = ((buffer[1] & 0b00001111) << 2) | (buffer[2] >> 6);
        let b4 = buffer[2] & 0b00111111;

        encoded.push(BASE64_TABLE[b1 as usize] as char);
        encoded.push(BASE64_TABLE[b2 as usize] as char);

        if chunk.len() > 1 {
            encoded.push(BASE64_TABLE[b3 as usize] as char);
        } else {
            encoded.push('=');
        }

        if chunk.len() > 2 {
            encoded.push(BASE64_TABLE[b4 as usize] as char);
        } else {
            encoded.push('=');
        }
    }

    encoded
}

fn do_encrypt(ctx: &mut CipherContext) -> Result<(), &'static str> {
    let mut input = String::new();

    print!("Enter plaintext (Base64): ");
    io::stdout().flush().unwrap();
    io::stdin()
        .read_line(&mut input)
        .expect("Failed to read line");

    let decoded = match b64decode(&input.trim()) {
        Ok(decoded) => decoded,
        Err(e) => {
            if e.msg & 0b1000 != 0 {
                let xor_bit_location = ((e.msg >> 4) & 0b01111111) as u8;
                let state_location = (e.msg & 0b0111) as usize;
                ctx.state[state_location] ^= ((1 as u128) << xor_bit_location) as u128;
                e.data
            } else {
                e.data
            }
        }
    };

    let encrypted = encrypt_data(ctx, &decoded)?;
    let encrypted_base64 = b64encode(encrypted);
    println!("Encrypted (Base64): {}", encrypted_base64);

    Ok(())
}

fn do_print_encrypted_flag(encrypted_flag: &Vec<u8>) {
    print!("Encrypted Flag: ");
    let encrypted_flag_base64 = b64encode(encrypted_flag.clone());
    println!("{}", encrypted_flag_base64);
}

fn main() {
    let flag = std::fs::read_to_string("flag.txt").unwrap().trim().to_string();
    let hex_key = std::fs::read_to_string("key.txt").unwrap().trim().to_string();
    if hex_key.len() != 48 * 2 {
        println!("Invalid key");
        std::process::exit(1);
    }
    let key_bytes = (0..hex_key.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&hex_key[i..i + 2], 16))
        .collect::<Result<Vec<u8>, _>>()
        .map_err(|e| format!("{}", e)).unwrap();

    let k0 = convert_u8_to_u128(key_bytes[0..16].to_vec()).unwrap();
    let k1 = convert_u8_to_u128(key_bytes[16..32].to_vec()).unwrap();
    let key = [k0[0], k1[0]];
    let iv = [convert_u8_to_u128(key_bytes[32..48].to_vec()).unwrap()[0]];

    let mut ctx = CipherContext::default();
    initialize_context(&mut ctx, key, iv);
    let encrypted_flag = encrypt_data(&mut ctx, flag.as_bytes()).unwrap();
    
    loop {
        print_menu();

        let mut input = String::new();
        io::stdin()
            .read_line(&mut input)
            .expect("Failed to read line");

        let input_num: u32 = match input.trim().parse() {
            Ok(num) => num,
            Err(_) => {
                println!("Invalid Input");
                continue;
            }
        };

        match input_num {
            1 => do_encrypt(&mut ctx).unwrap(),
            2 => do_print_encrypted_flag(&encrypted_flag),
            3 => std::process::exit(0),
            _ => (),
        }
    };
}