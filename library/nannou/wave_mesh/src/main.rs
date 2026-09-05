use nannou::prelude::*;

use std::collections::HashMap;
use std::net::UdpSocket;
use std::sync::{Arc, Mutex};
use std::sync::atomic::{AtomicU64, Ordering};
use std::thread;

struct Model {
    time: f32,
    osc: Arc<Mutex<HashMap<String, f32>>>,
    speed: f32,
    amplitude: f32,
    hue_shift: f32,
}

fn main() {
    nannou::app(model).update(update).run();
}

fn model(app: &App) -> Model {
    app.new_window()
        .size(1920, 1080)
        .view(view)
        .build()
        .unwrap();
    Model {
        time: 0.0,
        osc: osc_listen(9002),
        speed: 1.2,
        amplitude: 12.0,
        hue_shift: 0.05,
    }
}

fn update(_app: &App, model: &mut Model, _update: Update) {
    model.time += _update.since_last.secs() as f32;
    model.speed = osc_get(&model.osc, "/mesh/speed", model.speed);
    model.amplitude = osc_get(&model.osc, "/mesh/amplitude", model.amplitude);
    model.hue_shift = osc_get(&model.osc, "/mesh/hue", model.hue_shift);
}

fn view(app: &App, model: &Model, frame: Frame) {
    let draw = app.draw();
    draw.background().color(BLACK);

    let cols = 64;
    let rows = 40;
    let w = 1920.0;
    let h = 1080.0;
    let cell_w = w / cols as f32;
    let cell_h = h / rows as f32;

    let t = model.time;
    let spd = model.speed;
    let amp = model.amplitude;
    let hu = model.hue_shift;

    for j in 0..=rows {
        for i in 0..=cols {
            let x = -w / 2.0 + i as f32 * cell_w;
            let y = -h / 2.0 + j as f32 * cell_h;

            let fi = i as f32;
            let fj = j as f32;
            let z = (fi * 0.15 + t * spd).sin() * amp
                  + (fj * 0.12 + t * spd * 0.7).cos() * (amp * 0.83)
                  + ((fi + fj) * 0.08 + t * spd * 0.4).sin() * (amp * 0.67);

            let hue = (fi / cols as f32 * 0.3 + fj / rows as f32 * 0.2 + t * hu) % 1.0;
            let color = hsla(hue, 0.8, 0.5, 0.85);

            let sz = 2.0 + z.abs() * 0.15;
            draw.ellipse()
                .x_y(x, y + z)
                .w_h(sz, sz)
                .color(color);
        }
    }

    // horizontal lines
    for j in 0..=rows {
        let mut pts: Vec<Point2> = Vec::new();
        for i in 0..=cols {
            let x = -w / 2.0 + i as f32 * cell_w;
            let fi = i as f32;
            let fj = j as f32;
            let z = (fi * 0.15 + t * spd).sin() * amp
                  + (fj * 0.12 + t * spd * 0.7).cos() * (amp * 0.83)
                  + ((fi + fj) * 0.08 + t * spd * 0.4).sin() * (amp * 0.67);
            pts.push(pt2(x, -h / 2.0 + j as f32 * cell_h + z));
        }
        let hue = (j as f32 / rows as f32 * 0.4 + t * 0.03) % 1.0;
        draw.polyline()
            .weight(1.0)
            .color(hsla(hue, 0.7, 0.4, 0.5))
            .points(pts);
    }

    draw.to_frame(app, &frame).unwrap();
    frameout(app);
}

// --- XVCpanel in-terminal preview bridge: ~4 fps PNG; hidden window when XVC_HEADLESS ---
fn frameout(app: &App) {
    static LAST: AtomicU64 = AtomicU64::new(0);
    if std::env::var("XVC_HEADLESS").is_ok() {
        app.main_window().set_visible(false);
    }
    let ms = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_millis() as u64;
    let last = LAST.load(Ordering::Relaxed);
    if last != 0 && ms.saturating_sub(last) < 250 {
        return;
    }
    LAST.store(ms, Ordering::Relaxed);
    if let Ok(dir) = std::env::current_dir() {
        let d = dir.join("data");
        std::fs::create_dir_all(&d).ok();
        app.main_window().capture_frame(d.join("frame.png"));
    }
}

fn osc_listen(port: u16) -> Arc<Mutex<HashMap<String, f32>>> {
    let vals = Arc::new(Mutex::new(HashMap::new()));
    let v = vals.clone();
    thread::spawn(move || {
        let sock = match UdpSocket::bind(("0.0.0.0", port)) {
            Ok(s) => s,
            Err(e) => {
                eprintln!("OSC bind {port}: {e}");
                return;
            }
        };
        let mut buf = [0u8; 512];
        loop {
            if let Ok((n, _)) = sock.recv_from(&mut buf) {
                if let Some((addr, val)) = parse_osc(&buf[..n]) {
                    if let Ok(mut m) = v.lock() {
                        m.insert(addr, val);
                    }
                }
            } else {
                thread::sleep(std::time::Duration::from_millis(10));
            }
        }
    });
    vals
}

fn parse_osc(b: &[u8]) -> Option<(String, f32)> {
    let addr_end = b.iter().position(|&c| c == 0)?;
    let addr = String::from_utf8_lossy(&b[..addr_end]).to_string();
    if addr.is_empty() {
        return None;
    }
    let mut i = ((addr_end + 1 + 3) / 4) * 4;
    while i < b.len() && b[i] != 0 {
        i += 1;
    }
    i = ((i + 1 + 3) / 4) * 4;
    if i + 4 > b.len() {
        return None;
    }
    let val = f32::from_be_bytes([b[i], b[i + 1], b[i + 2], b[i + 3]]);
    Some((addr, val))
}

fn osc_get(vals: &Arc<Mutex<HashMap<String, f32>>>, addr: &str, def: f32) -> f32 {
    if let Ok(m) = vals.lock() {
        if let Some(&v) = m.get(addr) {
            return v;
        }
    }
    def
}
