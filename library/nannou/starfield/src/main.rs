use nannou::prelude::*;

struct Star {
    base_x: f32,
    base_y: f32,
    depth: f32,
    phase: f32,
}

struct Model {
    time: f32,
    stars: Vec<Star>,
}

fn main() {
    nannou::app::Builder::new(model)
        .update(update)
        .view(view)
        .size(1920, 1080)
        .run();
}

fn model(_app: &App) -> Model {
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
    Model { time: 0.0, stars }
}

fn update(_app: &App, model: &mut Model, _update: Update) {
    model.time += _update.since_last.secs() as f32;
}

fn view(app: &App, model: &Model, frame: Frame) {
    let draw = app.draw();
    draw.background().color(BLACK);

    let t = model.time;

    for s in &model.stars {
        let wob = (s.phase + t * (0.3 + s.depth * 0.8)).sin() * 8.0;
        let x = s.base_x + wob;
        let y = s.base_y + ((s.phase * 1.7) + t * (0.2 + s.depth * 0.5)).sin() * 6.0;
        let size = 1.0 + s.depth * 3.0;
        let tw = 0.3 + 0.7 * (0.5 + 0.5 * (s.phase + t * 1.5 + s.depth * 4.0).sin());
        let hue = (0.6 + s.depth * 0.25 + t * 0.02) % 1.0;
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
}
