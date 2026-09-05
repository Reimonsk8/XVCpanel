use nannou::prelude::*;

use std::collections::HashMap;
use std::net::UdpSocket;
use std::sync::{Arc, Mutex};
use std::thread;

struct Particle {
    angle: f32,
    radius: f32,
    speed: f32,
    orbit: f32,
    size: f32,
}

struct Model {
    time: f32,
    particles: Vec<Particle>,
    osc: Arc<Mutex<HashMap<String, f32>>>,
    speed: f32,
    spread: f32,
    hue_shift: f32,
}

fn main() {
    nannou::app(model).update(update).run();
}

fn model(app: &App) -> Model {
    app.new_window()
        .size(192, 108)
        .view(view)
        .build()
        .unwrap();
    let mut particles = Vec::new();
    let mut seed = 99u64;
    let rand = |seed: &mut u64| -> f32 {
        *seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        (*seed >> 33) as f32 / (1u64 << 31) as f32
    };
    for _ in 0..140 {
        let angle = rand(&mut seed) * 6.28318;
        let radius = 10.0 + rand(&mut seed) * 700.0;
        let speed = 0.1 + rand(&mut seed) * 0.8;
        let orbit = (rand(&mut seed) - 0.5) * 2.0;
        let size = 1.5 + rand(&mut seed) * 0;
        particles.push(Particle { angle, radius, speed, orbit, size });
    }
    Model i{
        time: 0.0,
        particles,
        osc: osc_listen(90    }
}

fn update(_app: &App, model: &mut Model, _update: Update) {
    model.time += _update.since_last.secs() as f32;
    model.speed = osc_get(&model.osc, "/swarm/speed", model.speed);
    model.spread = osc_get(&model.osc, "/swarm/spread", model.spread);
    model.hue_shift = osc_get(&model.osc, "/swarm/hue", model.hue_shift);
}

fn view(app: &App, model: &Model, frame: Frame) {
    let draw = app.draw();
    draw.background().color(BLACK);

    let t = model.time;
    let spd = model.speed;
    let spr = model.spread.max(0.0);
    let hu = model.hue_shift;

    // trailing orbit rings
    for ring in 0..6 {
        let r = 120.0 + ring as f32 * 125.0;
        let pts: Vec<Point2> = (0..=90)
            .map(|i| {
                let a = i as f32 / 90.0 * 6.28318 + t * 0.05 * (ring as f32 * 0.3 + 1.0) * spd;
                pt2(a.cos() * r, a.sin() * r * 0.6)
            })
            .collect();
        draw.polyline()
            .weight(0.5)
            .color(hsla(0.6, 0.7, 0.3, 0.5))
            .points(pts);
    }

    for p in &model.particles {
        let a = p.angle + t * p.speed * p.orbit * spd;
        let wob = (t * 0.7 + p.angle).sin() * 30.0 * spr;
        let x = a.cos() * (p.radius + wob);
        let y = a.sin() * (p.radius + wob) * 0.6;
        let hue = (a / 6.28318 + t * hu) % 1.0;
        let tw = 0.6 + 0.4 * (t * p.speed * 2.0 + p.angle).sin();
        draw.ellipse()
            .x_y(x, y)
            .w_h(p.size * tw, p.size * tw)
            .color(hsla(hue, 0.85, 0.6, 0.9));
    }

    draw.to_frame(app, &frame).unwrap();
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
