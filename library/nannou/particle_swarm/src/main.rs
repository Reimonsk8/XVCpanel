use nannou::prelude::*;

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
}

fn main() {
    nannou::app::Builder::new(model)
        .update(update)
        .view(view)
        .size(1920, 1080)
        .run();
}

fn model(_app: &App) -> Model {
    let mut particles = Vec::new();
    let mut seed = 99u64;
    let rand = |seed: &mut u64| -> f32 {
        *seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        (*seed >> 33) as f32 / (1u64 << 31) as f32
    };
    for _ in 0..140 {
        let angle = rand(&mut seed) * 6.28318;
        let radius = 80.0 + rand(&mut seed) * 700.0;
        let speed = 0.1 + rand(&mut seed) * 0.8;
        let orbit = (rand(&mut seed) - 0.5) * 2.0;
        let size = 1.5 + rand(&mut seed) * 4.0;
        particles.push(Particle { angle, radius, speed, orbit, size });
    }
    Model { time: 0.0, particles }
}

fn update(_app: &App, model: &mut Model, _update: Update) {
    model.time += _update.since_last.secs() as f32;
}

fn view(app: &App, model: &Model, frame: Frame) {
    let draw = app.draw();
    draw.background().color(BLACK);

    let t = model.time;

    // trailing orbit rings
    for ring in 0..6 {
        let r = 120.0 + ring as f32 * 125.0;
        let pts: Vec<Point2> = (0..=90)
            .map(|i| {
                let a = i as f32 / 90.0 * 6.28318 + t * 0.05 * (ring as f32 * 0.3 + 1.0);
                pt2(a.cos() * r, a.sin() * r * 0.6)
            })
            .collect();
        draw.polyline()
            .weight(0.5)
            .color(hsla(0.6, 0.7, 0.3, 0.5))
            .points(pts);
    }

    for p in &model.particles {
        let a = p.angle + t * p.speed * p.orbit;
        let wob = (t * 0.7 + p.angle).sin() * 30.0;
        let x = a.cos() * (p.radius + wob);
        let y = a.sin() * (p.radius + wob) * 0.6;
        let hue = (a / 6.28318 + t * 0.02) % 1.0;
        let tw = 0.6 + 0.4 * (t * p.speed * 2.0 + p.angle).sin();
        draw.ellipse()
            .x_y(x, y)
            .w_h(p.size * tw, p.size * tw)
            .color(hsla(hue, 0.85, 0.6, 0.9));
    }

    draw.to_frame(app, &frame).unwrap();
}
