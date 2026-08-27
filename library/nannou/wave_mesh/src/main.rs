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

    for j in 0..=rows {
        for i in 0..=cols {
            let x = -w / 2.0 + i as f32 * cell_w;
            let y = -h / 2.0 + j as f32 * cell_h;

            let fi = i as f32;
            let fj = j as f32;
            let z = (fi * 0.15 + t * 1.2).sin() * 12.0
                  + (fj * 0.12 + t * 0.8).cos() * 10.0
                  + ((fi + fj) * 0.08 + t * 0.5).sin() * 8.0;

            let hue = (fi / cols as f32 * 0.3 + fj / rows as f32 * 0.2 + t * 0.05) % 1.0;
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
            let z = (fi * 0.15 + t * 1.2).sin() * 12.0
                  + (fj * 0.12 + t * 0.8).cos() * 10.0
                  + ((fi + fj) * 0.08 + t * 0.5).sin() * 8.0;
            pts.push(pt2(x, -h / 2.0 + j as f32 * cell_h + z));
        }
        let hue = (j as f32 / rows as f32 * 0.4 + t * 0.03) % 1.0;
        draw.polyline()
            .weight(1.0)
            .color(hsla(hue, 0.7, 0.4, 0.5))
            .points(pts);
    }

    draw.to_frame(app, &frame).unwrap();
}
