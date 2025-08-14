import { SimplifyService } from './simplify.service';
import { take } from 'rxjs';

describe('SimplifyService', () => {
  let service: SimplifyService;

  beforeEach(() => {
    service = new SimplifyService();
  });

  it('should set and get simplified text', (done) => {
    service.setSimplifiedText('בדיקה');
    service.simplifiedText$.pipe(take(1)).subscribe(val => {
      expect(val).toBe('בדיקה');
      done();
    });
  });

  it('should activate simplifiedActive when text is set', (done) => {
    service.setSimplifiedText('טקסט');
    service.simplifiedActive$.pipe(take(1)).subscribe(val => {
      expect(val).toBeTrue();
      done();
    });
  });

  it('should set metrics', (done) => {
    const metrics = { readability: 1, complexity: 2, frequencyScore: 3, bert: 4 , berts: 5};
    service.setMetrics(metrics);
    service.metrics$.pipe(take(1)).subscribe(val => {
      expect(val).toEqual(metrics);
      done();
    });
  });

  it('should set trace', (done) => {
    const trace = { step: 123 };
    service.setTrace(trace);
    service.trace$.pipe(take(1)).subscribe(val => {
      expect(val).toEqual(trace);
      done();
    });
  });

  it('should set keywords', (done) => {
    const keywords = { section: ['מילת מפתח'] };
    service.setKeywords(keywords);
    service.keywords$.pipe(take(1)).subscribe(val => {
      expect(val).toEqual(keywords);
      done();
    });
  });

  it('should set baseline text', (done) => {
    service.setBaselineText('בסיס');
    service.baselineText$.pipe(take(1)).subscribe(val => {
      expect(val).toBe('בסיס');
      done();
    });
  });

  it('should clear all values', (done) => {
    service.setSimplifiedText('טקסט');
    service.setTrace({ some: 'trace' });
    service.setMetrics({ readability: 1, complexity: 2, frequencyScore: 3, bert: 4 , berts: 5 });
    service.clear();

    service.simplifiedText$.pipe(take(1)).subscribe(val => {
      expect(val).toBe('');
    });
    service.simplifiedActive$.pipe(take(1)).subscribe(val => {
      expect(val).toBeFalse();
    });
    service.metrics$.pipe(take(1)).subscribe(val => {
      expect(val).toBeNull();
      done();
    });
  });
});
