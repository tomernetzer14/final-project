import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HomeComponent } from './home.component';

describe('HomeComponent', () => {
  let component: HomeComponent;
  let fixture: ComponentFixture<HomeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [HomeComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(HomeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should set showApp to true when startApp is called', () => {
    component.startApp();
    expect(component.showApp).toBeTrue();
  });

  it('should set showApp to false when goBackToIntro is called', () => {
    component.goBackToIntro();
    expect(component.showApp).toBeFalse();
  });
});
