use nannou::prelude::*;

use std::collections::HashMap;
use std::net::UdpSocket;
use std::sync::{Arc, Mutex};
use std::thread;

struct Model {
    time: f32,
    osc: Arc<Mutex<HashMap<String, f32>>>,
    flow: f32,
    bands: f32,
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
        osc: osc_listen(9008),
        flow: 0.5,
        bands: 5.0,
        hue_shift: 0.01,
    }
}

fn update(_app: &App, model: &mut Model, _update: Update) {
    model.time += _update.since_last.secs() as f32;
    model.flow = osc_get(&model.osc, "/aurora/flow", model.flow);
    model.bands = osc_get(&model.osc, "/aurora/bands", model.bands);
    model.hue_shift = osc_get(&model.osc, "/aurora/hue", model.hue_shift);
}

fn band_y(band: f32, x: f32, t: f32, flow: f32) -> f32 {
    let nx = x / 2000.0;
    (nx * 2.5 + t * (0.4 + band * 0.2) * flow + band * 7.0).sin() * 90.0
        + (nx * 6.0 - t * 0.6 * flow + band * 3.0).sin() * 30.0
}

fn view(app: &App, model: &Model, frame: Frame) {
    let draw = app.draw();
    draw.background().color(rgba(0.0, 0.01, 0.05, 1.0));

    let t = model.time;
    let flow = model.flow;
    let bands = model.bands.max(1.0).min(8.0) as u32;
    let hu = model.hue_shift;
    let cols = 120;

    for b in 0..bands {
        let f = b as f32;
        let base_y = -120.0 + f * 110.0;
        // glow layers
        for layer in 0..3 {
            let l = layer as f32;
            let pts: Vec<Point2> = (0..=cols)
                .map(|i| {
                    let x = -960.0 + i as f32 / cols as f32 * 1920.0;
                    let y = base_y + band_y(f, x, t, flow) + l * 14.0 * (f + 1.0);
                    pt2(x, y)
                })
                .collect();
            let hue = (0.55 + f * 0.12 + t * hu) % 1.0;
            draw.polyline()
                .weight(28.0 - l * 8.0)
                .color(hsla(hue, 0.7, 0.5, 0.05 + l * 0.04))
                .points(pts);
        }
        // bright core
        let pts: Vec<Point2> = (0..=cols)
            .map(|i| {
                let x = -960.0 + i as f32 / cols as f32 * 1920.0;
                let y = base_y + band_y(f, x, t, flow);
                pt2(x, y)
            })
            .collect();
        let hue = (0.55 + f * 0.12 + t * hu) % 1.0;
        draw.polyline()
            .weight(3.0)
            .color(hsla(hue, 0.9, 0.75, 0.9))
            .points(pts);
    }

    // stars
    for i in 0..60 {
        let x = -(i as f32 * 61.0 % 1920.0) + 960.0;
        let y = (i as f32 * 173.0 % 400.0) + 350.0;
        let tw = 0.5 + 0.5 * (t * 1.2 + i as f32).sin();
        draw.ellipse()
            .x_y(x, y)
            .w_h(1.5, 1.5)
            .color(hsla(0.6, 0.5, 0.9, tw));
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
