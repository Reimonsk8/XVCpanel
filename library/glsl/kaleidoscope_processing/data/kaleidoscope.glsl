// XVCpanel - Kaleidoscope (Processing GLSL)

#ifdef GL_ES
precision mediump float;
#endif

uniform vec2 resolution;
uniform float time;

vec3 palette(float t) {
    return 0.5 + 0.5 * cos(6.28318 * (vec3(0.02, 0.22, 0.48) + t));
}

void main() {
    vec2 p = (2.0 * gl_FragCoord.xy - resolution.xy) / resolution.y;
    float radius = length(p);
    float angle = atan(p.y, p.x) + time * 0.12;
    float sectors = 12.0;
    angle = abs(fract(angle / 6.28318 * sectors) - 0.5) * 2.0;
    float wave = sin(radius * 18.0 - time * 2.0 + angle * 8.0);
    float pattern = 0.5 + 0.5 * wave;
    vec3 color = palette(pattern + radius * 0.18 + time * 0.03);
    color *= smoothstep(1.6, 0.15, radius);
    gl_FragColor = vec4(color, 1.0);
}
