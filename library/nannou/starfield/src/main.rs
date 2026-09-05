use nannou::prelude::*;

use std::collections::HashMap;
use std::net::UdpSocket;
use std::sync::{Arc, Mutex};
use std::sync::atomic::{AtomicU64, Ordering};
use std::thread;

struct Star {
    base_x: f32,
    base_y: f32,
    depth: f32,
    phase: f32,
}

struct Model {
    time: f32,
    stars: Vec<Star>,
    osc: Arc<Mutex<HashMap<String, f32>>>,
    twinkle: f32,
    drift: f32,
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
    let mut stars = Vec::new();
    let mut seed = 12345u64;
    for _ in 0..220 {
        seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        let r1 = (seed >> 33) as f64 / (1u64 << 31) as f64;
        seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        let r2 = (seed >> 33) as f64 / (1u64 << 31) as f64;
        seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        let r3 = (seed >> 33) as f64 / (1u64 << 31) as f64;
        let base_x = (r1 as f32 - 0.5) * 2200.0;
        let base_y = (r2 as f32 - 0.5) * 1300.0;
        let depth = 0.2 + r3 as f32 * 1.0;
        let phase = r1 as f32 * 6.28318;
        stars.push(Star { base_x, base_y, depth, phase });
    }
    Model {
        time: 0.0,
        stars,
        osc: osc_listen(9007),
        twinkle: 1.5,
        drift: 0.4,
        hue_shift: 0.02,
    }
}

fn update(_app: &App, model: &mut Model, _update: Update) {
    model.time += _update.since_last.secs() as f32;
    model.twinkle = osc_get(&model.osc, "/star/twinkle", model.twinkle);
    model.drift = osc_get(&model.osc, "/star/drift", model.drift);
    model.hue_shift = osc_get(&model.osc, "/star/hue", model.hue_shift);
}

fn view(app: &App, model: &Model, frame: Frame) {
    let draw = app.draw();
    draw.background().color(BLACK);

    let t = model.time;
    let twk = model.twinkle;
    let drf = model.drift;
    let hu = model.hue_shift;

    for s in &model.stars {
        let wob = (s.phase + t * (0.3 + s.depth * 0.8) * drf).sin() * 8.0;
        let x = s.base_x + wob;
        let y = s.base_y + ((s.phase * 1.7) + t * (0.2 + s.depth * 0.5) * drf).sin() * 6.0;
        let size = 1.0 + s.depth * 3.0;
        let tw = 0.3 + 0.7 * (0.5 + 0.5 * (s.phase + t * twk + s.depth * 4.0).sin());
        let hue = (0.6 + s.depth * 0.25 + t * hu) % 1.0;
        draw.ellipse()
            .x_y(x, y)
            .w_h(size, size)
            .color(hsla(hue, 0.8, 0.5 + tw * 0.4, tw));
    }

    // occasional shooting streak
    let streak_progress = (t * 0.08).fract();
    let sx = -1000.0 + streak_progress * 2500.0;
    let sy = (t * 2.0).sin() * 400.0;
    for i in 0..40 {
        let f = i as f32 / 39.0;
        draw.line()
            .start(pt2(sx - f * 300.0, sy - f * 120.0))
            .end(pt2(sx - (f - 0.1) * 300.0, sy - (f - 0.1) * 120.0))
            .weight(1.0)
            .color(hsla(0.6, 0.8, 0.9, (1.0 - f) * 0.6));
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
