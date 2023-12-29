fn step(input: String) -> String {
    let mut chars: Vec<char> = input.chars().collect();
    let mut a = chars.pop();

    match a {
        Some(x) => format!("{}{}", x, step(chars.into_iter().collect())).to_string(),
        None    => "".to_owned()
    }
}