// XVCpanel - Kaleidoscope (Processing GLSL) - OSC controlled

#ifdef GL_ES
precision mediump float;
#endif

uniform vec2 resolution;
uniform float time;
uniform float sectors;
uniform float rotateSpeed;
uniform float colorShift;

vec3 palette(float t) {
    return 0.5 + 0.5 * cos(6.28318 * (vec3(0.02, 0.22, 0.48) + t));
}

void main() {
    vec2 p = (2.0 * gl_FragCoord.xy - resolution.xy) / resolution.y;
    float radius = length(p);
    float angle = atan(p.y, p.x) + time * rotateSpeed;
    float s = max(sectors, 0.1);
    angle = abs(fract(angle / 6.28318 * s) - 0.5) * 2.0;
    float wave = sin(radius * 18.0 - time * 2.0 + angle * 8.0);
    float pattern = 0.5 + 0.5 * wave;
    vec3 color = palette(pattern + radius * 0.18 + time * colorShift * 0.12);
    color *= smoothstep(1.6, 0.15, radius);
    gl_FragColor = vec4(color, 1.0);
}
