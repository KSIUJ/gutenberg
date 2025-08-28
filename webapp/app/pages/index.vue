<template>
  <sidebar-layout>
    <template #sidebar>
      <app-panel
        v-if="$auth.me.value === Unauthenticated"
        ghost
        class="grow"
      >
        <div class="grow flex flex-col items-center justify-center text-center space-y-4">
          <div>
            Sign in to print documents online
          </div>
          <!--
             The sign in button is not a NuxtLink, because the /login/ route might be handled by Django,
             not Vue Router, if OIDC sign-in is enabled.
           -->
          <p-button
            label="Sign in"
            as="a"
            href="/login/"
            size="large"
          />
        </div>
      </app-panel>

      <div
        v-else
        class="space-y-4 flex flex-col grow"
      >
        <print-options />

        <!--        <app-panel header="Recently printed" class="grow"> -->
        <!--          <div class="text-muted-color text-center p-6">This feature is not yet implemented</div> -->
        <!--        </app-panel> -->
      </div>
    </template>

    <template #content>
      <app-content>
        <h1>Other ways to print</h1>
        <h2>IPP</h2>
        <div class="space-y-6 mt-4 text-justify text-sm text-muted-color">
          <p>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus vel luctus ante, vel dictum odio. Morbi posuere mi in lacus semper, at sollicitudin elit sodales. Interdum et malesuada fames ac ante ipsum primis in faucibus. Ut neque sapien, efficitur ut justo eu, luctus tempor urna. Vivamus a mollis lectus. Fusce lacinia et purus ac maximus. Donec facilisis, nibh in tempus sollicitudin, velit sem pharetra ligula, a accumsan odio tellus in tortor. Donec condimentum tortor eu arcu pretium, id elementum tellus porttitor. Mauris in ultricies eros. Sed pretium justo nec congue molestie.
          </p>
          <p>
            Quisque id massa in nunc sodales lobortis in at ante. Proin vulputate dolor vel magna egestas pellentesque. Aliquam augue tortor, faucibus vel imperdiet in, imperdiet nec felis. Etiam vestibulum fringilla imperdiet. Vivamus nibh sem, consectetur id aliquet sodales, mollis eu nibh. Cras sit amet vulputate nulla, lacinia vestibulum mauris. Donec pellentesque ligula posuere orci eleifend elementum. Maecenas quis nulla ut sem cursus commodo id et ligula.
          </p>
          <p>
            Integer id erat bibendum, aliquam diam quis, porttitor justo. Aenean eu congue magna. Cras molestie tempor pharetra. Donec accumsan magna nec mollis egestas. Cras rutrum metus nulla, eu tincidunt odio dignissim vulputate. Aenean ac accumsan nulla. Nullam tincidunt malesuada tortor a venenatis. Suspendisse maximus magna vitae hendrerit hendrerit. Maecenas viverra ligula id maximus ullamcorper. Praesent nisi ipsum, faucibus ac tempor ultricies, convallis ac sapien.
          </p>
          <p>
            Sed convallis aliquam justo tristique feugiat. Phasellus imperdiet finibus condimentum. Mauris vitae dolor at enim sodales luctus. Sed ut posuere dolor. Donec nec mi dignissim, vehicula nibh tristique, fringilla libero. Curabitur tempus eros augue, eget mattis odio gravida a. Aliquam erat volutpat. Donec malesuada dapibus orci ac porttitor. Aliquam efficitur, lacus sit amet imperdiet suscipit, urna ex faucibus urna, eget aliquam nibh arcu eu nisi. Vivamus sit amet mi est.
          </p>
          <p>
            Donec consectetur risus orci, vel dapibus metus ultrices sit amet. Aliquam maximus turpis tempor, lobortis purus non, posuere orci. Vestibulum commodo molestie mauris, molestie placerat enim commodo sed. Etiam hendrerit vulputate vestibulum. Proin vitae odio scelerisque, gravida sapien eget, consectetur lacus. Nulla facilisi. Proin tristique sapien arcu, ut semper sem consectetur eget. Suspendisse enim sem, condimentum quis justo quis, porttitor sollicitudin orci. Aliquam sed dictum neque, tristique consequat urna. Quisque id bibendum eros. Nulla vestibulum id enim sit amet egestas. Maecenas consequat elit convallis dui blandit faucibus. Phasellus eget tortor at dui venenatis fermentum ac at dui. Vestibulum nisi odio, facilisis et ex dictum, tristique elementum tellus. Nullam mollis velit libero, non luctus odio rhoncus ut. Vestibulum odio felis, imperdiet sed tempus vel, viverra commodo nunc.
          </p>
          <p>
            Vivamus blandit tincidunt neque, ac varius libero. Vivamus tortor augue, interdum et erat ut, ultrices vestibulum leo. Maecenas laoreet blandit sollicitudin. Nam placerat dui a nunc vehicula fringilla. Ut vulputate dolor sit amet suscipit pulvinar. Aliquam tellus felis, congue vitae erat ac, commodo dapibus augue. Proin libero arcu, laoreet a faucibus nec, bibendum a lorem. Duis a ante iaculis, semper mauris id, sagittis nisl. Phasellus convallis quam quis nulla ultricies, vitae venenatis dui malesuada. Aliquam aliquet, neque quis feugiat tempus, justo leo vestibulum arcu, quis consequat diam diam ac tortor. Aliquam vel nisl eleifend felis pharetra laoreet. Pellentesque elementum dignissim lectus in euismod. Aenean magna ipsum, volutpat nec arcu eu, fringilla convallis orci. Interdum et malesuada fames ac ante ipsum primis in faucibus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Ut quis lorem eu ante sollicitudin maximus.
          </p>
          <p>
            Nam ac metus felis. Nulla venenatis ligula vitae elit ultrices porta. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Suspendisse nec rhoncus mauris, nec ultrices diam. Nulla facilisis malesuada orci, quis elementum erat. Nulla in molestie sem. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Pellentesque laoreet, nisi at consequat egestas, magna erat faucibus orci, sit amet porta mauris ex eget risus. Curabitur elementum convallis porttitor. Ut auctor ut urna vitae sagittis.
          </p>
          <p>
            Nullam tempus lacinia purus a fermentum. Nunc luctus ultricies luctus. Curabitur in leo fermentum velit sollicitudin finibus sit amet in nisl. Maecenas sed leo vel nunc auctor efficitur. Mauris a cursus leo. Vestibulum eleifend malesuada pretium. Sed id eros arcu.
          </p>
          <p>
            Pellentesque ac velit dui. Suspendisse blandit facilisis ultrices. In eu orci rutrum erat accumsan vestibulum id sed ipsum. Suspendisse varius risus arcu, nec porta purus mollis a. Praesent nibh elit, vestibulum eu velit eget, feugiat malesuada eros. Vestibulum venenatis purus in mauris rhoncus faucibus. Integer at nisi quis quam mollis commodo sit amet in mauris. Donec fringilla tellus mauris, vel tincidunt dui porta a.
          </p>
          <p>
            Nam a malesuada libero, ac convallis erat. Integer sed nulla vel lorem mattis rutrum eget id diam. Etiam quis lectus sagittis, suscipit sapien quis, varius metus. In hac habitasse platea dictumst. Suspendisse non sagittis risus. Cras sit amet elit sagittis purus ultricies tempus. Praesent nec feugiat urna.
          </p>
        </div>
      </app-content>
    </template>
  </sidebar-layout>
</template>

<script setup lang="ts">
const { $auth } = useNuxtApp();
</script>
