use nannou::prelude::*;

struct Model {
    time: f32,
}

fn main() {
    nannou::app::Builder::new(model)
        .update(update)
        .view(view)
        .size(1920, 1080)
        .run();
}

fn model(_app: &App) -> Model {
    Model { time: 0.0 }
}

fn update(_app: &App, model: &mut Model, _update: Update) {
    model.time += _update.since_last.secs() as f32;
}

fn band_y(band: f32, x: f32, t: f32) -> f32 {
    let nx = x / 2000.0;
    (nx * 2.5 + t * (0.4 + band * 0.2) + band * 7.0).sin() * 90.0
        + (nx * 6.0 - t * 0.6 + band * 3.0).sin() * 30.0
}

fn view(app: &App, model: &Model, frame: Frame) {
    let draw = app.draw();
    draw.background().color(rgba(0.0, 0.01, 0.05, 1.0));

    let t = model.time;
    let bands = 5;
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
                    let y = base_y + band_y(f, x, t) + l * 14.0 * (f + 1.0);
                    pt2(x, y)
                })
                .collect();
            let hue = (0.55 + f * 0.12 + t * 0.01) % 1.0;
            draw.polyline()
                .weight(28.0 - l * 8.0)
                .color(hsla(hue, 0.7, 0.5, 0.05 + l * 0.04))
                .points(pts);
        }
        // bright core
        let pts: Vec<Point2> = (0..=cols)
            .map(|i| {
                let x = -960.0 + i as f32 / cols as f32 * 1920.0;
                let y = base_y + band_y(f, x, t);
                pt2(x, y)
            })
            .collect();
        let hue = (0.55 + f * 0.12 + t * 0.01) % 1.0;
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
